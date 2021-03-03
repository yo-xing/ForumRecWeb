import streamlit as st
import requests
import asyncio
from authlib.integrations import requests_client

from stackapi import StackAPI

AUTH_BASE_URL = "https://stackexchange.com/oauth"
TOKEN_URL = "https://stackoverflow.com/oauth/access_token/json"
CLIENT_ID = "19673"
CLIENT_SECRET =  "Ftm5ijUJpb7TUEb3jBNTyw(("
SECRET_KEY = "nIFln5DrNi7grh*o22xAIw(("

st.title("ForumRec")
st.sidebar.title("User Profile")
login_button = st.button("Login to Super User")

if login_button:
    superuser = requests_client.OAuth2Session(CLIENT_ID, redirect_uri="http://localhost:8501/callback")
    auth_url, _ = superuser.create_authorization_url(AUTH_BASE_URL)
    st.write(auth_url)

    superuser = requests_client.OAuth2Session(CLIENT_ID)
    token = superuser.fetch_token(
        url=TOKEN_URL, client_secret=CLIENT_SECRET, \
        authorization_response=auth_url, \
        redirect_uri="http://localhost:8501/callback"
    )
    st.write(token)

    asyncio.run(write_access_token(code))
    # superuser = requests_client.OAuth2Session(CLIENT_ID, redirect_uri="http://localhost:8501/callback")
    # auth_url, _ = superuser.create_authorization_url(AUTH_BASE_URL)
    # requests.redirect(auth_url)

    # superuser = requests_client.OAuth2Session(CLIENT_ID)
    # token = superuser.fetch_token(
    # 	url=TOKEN_URL, client_secret=CLIENT_SECRET, \
    #     authorization_response=auth_url, \
    #     redirect_uri="http://localhost:8501/callback"
	# )

    # # SITE = StackAPI('superuser', key=SECRET_KEY)
    # # me = SITE.fetch('me', access_token=token['access_token'])

    # # Keep user_id, profile_image, display_name

    # st.write(str(token))