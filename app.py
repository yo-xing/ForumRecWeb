import flask
from authlib.integrations import requests_client
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
CLIENT_SECRET =  ""
SECRET_KEY = ""

app = flask.Flask(__name__, template_folder='templates')

@app.route('/', methods=['GET', 'POST'])
def main():
    flask.render_template('main.html')
    return """
        <a href="/login">Login with StackExchange: SuperUser</a>
    """

@app.route('/login')
def login():
    superuser = requests_client.OAuth2Session(CLIENT_ID, redirect_uri="http://jackzlin.com/callback")
    #superuser = requests_client.OAuth2Session(CLIENT_ID, redirect_uri="http://localhost:5000/callback")
    auth_url, _ = superuser.create_authorization_url(AUTH_BASE_URL)

    return flask.redirect(auth_url)

@app.route('/callback')
def callback():

    superuser = requests_client.OAuth2Session(CLIENT_ID)
    token = superuser.fetch_token(
    	url=TOKEN_URL, client_secret=CLIENT_SECRET, \
        authorization_response=flask.request.url, \
        redirect_uri="http://jackzlin.com/callback" )
        #redirect_uri="http://localhost:5000/callback" )

    SITE = StackAPI('superuser', key=SECRET_KEY)
    me = SITE.fetch('me', access_token=token['access_token'])

    # Keep user_id, profile_image, display_name

    return flask.json.jsonify(me)

@app.route('/', methods=['GET', 'POST'])
def get_data():
    returnVal = requests.get('https://stackexchange.com/oauth/dialog?client_id=19673&scope=&redirect_uri=http://jackzlin.com/').content
    #returnVal = requests.get('https://stackexchange.com/oauth/dialog?client_id=19673&scope=&redirect_uri=http://localhost:5000/').content
    print(returnVal)
    return returnVal

if __name__ == '__main__':
    app.run(debug=True)
