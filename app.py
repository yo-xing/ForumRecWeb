import flask
from authlib.integrations import requests_client
import requests
import pickle
import sys
import os

from stackapi import StackAPI

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


# Use pickle to load in model
# with open(f'model/first_model.pkl', 'rb') as f:
#     model = pickle.load(f)

AUTH_BASE_URL = "https://stackexchange.com/oauth"
TOKEN_URL = "https://stackoverflow.com/oauth/access_token/json"
CLIENT_ID = "19673"
CLIENT_SECRET =  "Ftm5ijUJpb7TUEb3jBNTyw(("
SECRET_KEY = "nIFln5DrNi7grh*o22xAIw(("
USER_VALS = None

app = flask.Flask(__name__, template_folder='templates')

@app.route('/', methods=['GET', 'POST'])
def main():
    if flask.request.method == 'GET':
        return flask.render_template('main.html')
    
    if flask.request.method == 'POST':
        answers = flask.request.form.getlist("question")
        userId = USER_VALS['user_id']
        return flask.render_template('main.html', userId=userId, userItems=USER_VALS, ans=answers)


    # Click get recommendations
    # Run API Script (Or Run on website start)
    # Send API Data to Firebase
    # Gather Data From Firebase to send to model
    # Run Model with Data
    # Send Updated Results to Firebase
    # Return updated results to user


@app.route('/login')
def login():
    superuser = requests_client.OAuth2Session(CLIENT_ID, redirect_uri="http://localhost:5000/callback")
    auth_url, _ = superuser.create_authorization_url(AUTH_BASE_URL)

    return flask.redirect(auth_url)

@app.route('/callback')
def callback():
    
    superuser = requests_client.OAuth2Session(CLIENT_ID)
    token = superuser.fetch_token(
    	url=TOKEN_URL, client_secret=CLIENT_SECRET, \
        authorization_response=flask.request.url, \
        redirect_uri="http://localhost:5000/callback"
	)

    SITE = StackAPI('superuser', key=SECRET_KEY)
    me = SITE.fetch('me', access_token=token['access_token'])

    # Keep user_id, profile_image, display_name
    global USER_VALS
    USER_VALS = me['items'][0]
    userId = USER_VALS['user_id']

    return flask.render_template('main.html', userId=userId, userItems=USER_VALS)

@app.route('/recommendations')
def recommendations():
    userId = USER_VALS['user_id']
    top_questions_list = ['Yes', 'Sir', 'We', 'Are', 'Doing', 'It']
    user_questions_data = {'New': [1298302, 1629649], 'Previous':[1629646]}
    all_questions_data = {1298302: ['How to access my Raspberry Pi remotely?', 'https://superuser.com/questions/1298302'], 
            1629649: ['Recovering a deleted text message on Android', 'https://superuser.com/questions/1629649'],
            1629646: ['What is the regex to find and move', 'https://superuser.com/questions/1629646']}
    data_avail = True

    return flask.render_template('main.html', userId=userId, userItems=USER_VALS, coldStart=True, userData=data_avail,
                                    topQList=top_questions_list, userQList=user_questions_data, qList=all_questions_data)

@app.route('/', methods=['GET', 'POST'])
def get_data():
    returnVal = requests.get('https://stackexchange.com/oauth/dialog?client_id=19673&scope=&redirect_uri=http://localhost:5000/').content
    print(returnVal)
    return returnVal

if __name__ == '__main__':
    app.run(debug=True)
