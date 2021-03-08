import flask
from authlib.integrations import requests_client
import requests
import psycopg2
import pickle
import pandas as pd
import sys
import os
from io import StringIO
import boto3

import new_user


from stackapi import StackAPI

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Set up connection to RDS db
connection = psycopg2.connect(
    host = 'forumrec-db.clb5kddz8xbd.us-west-1.rds.amazonaws.com',
    port = 5432,
    user = 'ForumRecAdmin',
    password = 'ForumRecTest',
    database = 'postgres')
cursor = connection.cursor()

# Use pickle to load in model
# with open(f'model/first_model.pkl', 'rb') as f:
#     model = pickle.load(f)

AUTH_BASE_URL = "https://stackexchange.com/oauth"
TOKEN_URL = "https://stackoverflow.com/oauth/access_token/json"
CLIENT_ID = "19673"
CLIENT_SECRET =  "Ftm5ijUJpb7TUEb3jBNTyw(("
SECRET_KEY = "nIFln5DrNi7grh*o22xAIw(("
SPLIT_DATE = 1514764800
# FILTER = '!.FjwPGLxmyYTgEFmTS8QjLMHj6rLP '
USER_VALS = None

app = flask.Flask(__name__, template_folder='templates')

@app.route('/', methods=['GET', 'POST'])
def main():
    if flask.request.method == 'GET':
        return flask.render_template('main.html')
    
    if flask.request.method == 'POST':
        answers = flask.request.form.getlist("question")
        userId = USER_VALS['user_id']
        # Write these answers data into the database as the cold-start questions to answer
        # Create model as well
        # Potentially add progress bar

        query_top_pop = """
        SELECT *
        FROM COLDQUESTIONS
        """

        # If not cold user, get their data and write it into the manner commented out below

        cold_df = pd.read_sql(query_top_pop, con=connection)[['id']]
        cold_df['OwnerUserId'] = pd.Series([userId for _ in range(cold_df.shape[0])])
        cold_df['Score'] = cold_df.id.apply(lambda x: 1 if x in answers else 0)

        # Reorder and rename columns
        cold_df.columns = ['ParentId', 'OwnerUserId', 'Score']
        cold_df = cold_df[['OwnerUserId', 'ParentId', 'Score']]

        # Write to s3
        bucket = "forumrecbucket"
        csv_buffer = StringIO()
        cold_df.to_csv(csv_buffer, index=False)
            
        s3_resource = boto3.resource('s3')
        s3_resource.Object(bucket, 'new_sample.csv').put(Body=csv_buffer.getvalue())

        # get csv from s3
        # csv_obj = client.get_object(Bucket=bucket_name, Key=object_key)['Body'].read().decode('utf-8')
        # df = pd.read_csv(StringIO(csv_obj))
        
        new_user.main()
        
        return flask.render_template('main.html', userId=userId, userItems=USER_VALS, ans=answers)

    # Run API Script (Or Run on website start)
    # Send API Data to Firebase
    # Gather Data From Firebase to send to model
    # Run Model with Data
    # Send Updated Results to Firebase
    # Return updated results to user

    # top_questions_list = ['Yes', 'Sir', 'We', 'Are', 'Doing', 'It']
    # user_questions_data = {'New': [1298302, 1629649], 'Previous':[1629646]}
    # all_questions_data = {1298302: ['How to access my Raspberry Pi remotely?', 'https://superuser.com/questions/1298302'], 
    #         1629649: ['Recovering a deleted text message on Android', 'https://superuser.com/questions/1629649'],
    #         1629646: ['What is the regex to find and move', 'https://superuser.com/questions/1629646']}


@app.route('/login')
def login():
    # superuser = requests_client.OAuth2Session(CLIENT_ID, redirect_uri="https://jackzlin.com/callback")
    superuser = requests_client.OAuth2Session(CLIENT_ID, redirect_uri="http://localhost:5000/callback")
    auth_url, _ = superuser.create_authorization_url(AUTH_BASE_URL)

    return flask.redirect(auth_url)

@app.route('/callback')
def callback():

    superuser = requests_client.OAuth2Session(CLIENT_ID)
    token = superuser.fetch_token(
    	url=TOKEN_URL, client_secret=CLIENT_SECRET, \
        authorization_response=flask.request.url, \
        # redirect_uri="https://jackzlin.com/callback" )
        redirect_uri="http://localhost:5000/callback" )

    SITE = StackAPI('superuser', key=SECRET_KEY)
    me = SITE.fetch('me', access_token=token['access_token'])

    # Keep user_id, profile_image, display_name
    global USER_VALS
    USER_VALS = me['items'][0]
    userId = USER_VALS['user_id']

    # Get users with cold start
    query_users_cold = """
    SELECT *
    FROM USERS
    """
    
    cold_users = pd.read_sql(query_users_cold, con=connection)

    # Set of cold_users
    if userId in set(cold_users.user_id):
        pass
    
    else:
        answered_questions = SITE.fetch('me/answers', access_token=token['access_token'], fromdate=SPLIT_DATE)

        try:
            len_questions = len(answered_questions['items']['answers'])
        except:
            len_questions = 0

        if len_questions < 25:
            insert_cold = """
            INSERT INTO USERS (user_id, name, profile_img_url, cold)
            VALUES ({0}, '{1}', '{2}', TRUE)
            """.format(userId, USER_VALS['display_name'], USER_VALS['profile_image'])
            
        else:
            insert_cold = """
            INSERT INTO USERS (user_id, name, profile_img_url, cold)
            VALUES ({0}, '{1}', '{2}', FALSE)
            """.format(userId, USER_VALS['display_name'], USER_VALS['profile_image'])
        
        cursor.execute(insert_cold)
        connection.commit()

    return flask.render_template('main.html', userId=userId, userItems=USER_VALS)

@app.route('/recommendations')
def recommendations():
    userId = USER_VALS['user_id']
    
    query_cold_start = """
    SELECT COLD
    FROM USERS
    WHERE USER_ID = {0}
    """.format(userId)

    is_cold = pd.read_sql(query_cold_start, con=connection).cold[0] 

    # if cold_users.cold: 
    #     pass
    #grab user from database 
    query_top_pop = """
    SELECT *
    FROM COLDQUESTIONS
    """

    # If not cold user, get their data and write it into the manner commented out below

    top_questions_list = pd.read_sql(query_top_pop, con=connection).sample(100).values.tolist()
    # user_questions_data = {'New': [1298302, 1629649], 'Previous':[1629646]}
    # all_questions_data = {1298302: ['How to access my Raspberry Pi remotely?', 'https://superuser.com/questions/1298302'], 
    #         1629649: ['Recovering a deleted text message on Android', 'https://superuser.com/questions/1629649'],
    #         1629646: ['What is the regex to find and move', 'https://superuser.com/questions/1629646']}
    
    data_avail = False

    return flask.render_template('main.html', userId=userId, userItems=USER_VALS, coldStart=is_cold, userData=data_avail,
                                    topQList=top_questions_list)
                                    #, userQList=user_questions_data, qList=all_questions_data)

@app.route('/about')
def about():
    # Check to display login information
    if USER_VALS:
        userId = USER_VALS['user_id']
    else:
        userId = None
    
    userItems = USER_VALS

    # Display about page
    return flask.render_template('about.html', userId=userId, userItems=userItems)

if __name__ == '__main__':
    app.run(debug=True)
