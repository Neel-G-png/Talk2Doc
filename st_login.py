import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import os
import json
import requests
import logging

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Configuration
CLIENT_SECRETS_FILE = "credentials/client_secrets.json"
SCOPES = ["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"]
REDIRECT_URI = "http://localhost:8501"

# Initialize session state
if "credentials" not in st.session_state:
    st.session_state.credentials = None

# Load Google OAuth client secrets from a file
def load_client_secrets():
    if not os.path.exists(CLIENT_SECRETS_FILE):
        st.error(f"Missing {CLIENT_SECRETS_FILE}. Ensure it's in the same directory as this script.")
        st.stop()
    with open(CLIENT_SECRETS_FILE, "r") as file:
        return json.load(file)

# Step 1: Display login link
def create_flow():
    client_secrets = load_client_secrets()
    flow = Flow.from_client_config(
        client_secrets,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    return flow

# Main app logic
st.title("Login with Google")

if st.session_state.credentials is None:
    # Display login link if no credentials
    flow = create_flow()
    auth_url, _ = flow.authorization_url(prompt="consent")
    st.markdown(f"[Click here to log in with Google]({auth_url})")

# Step 2: Handle the authorization response
query_params = st.query_params

if "code" in query_params and st.session_state.credentials is None:
    # Extract authorization code from query parameters
    code = query_params["code"]
    flow = create_flow()
    auth_response_url = f"{REDIRECT_URI}?code={code}"
    try:
        flow.fetch_token(authorization_response=auth_response_url)
        st.session_state.credentials = flow.credentials
        st.success("Authentication successful!")
    except Exception as e:
        st.error(f"Failed to fetch token: {e}")
        st.stop()

# Step 3: Fetch and display user info
if st.session_state.credentials:
    try:
        # Initialize credentials
        credentials = st.session_state.credentials
        creds = Credentials(
            token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_uri=credentials.token_uri,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            scopes=credentials.scopes,
        )

        # Fetch user info
        userinfo_endpoint = "https://www.googleapis.com/oauth2/v3/userinfo"
        response = requests.get(userinfo_endpoint, headers={"Authorization": f"Bearer {creds.token}"})
        
        if response.status_code == 200:
            user_info = response.json()
            st.success("You are logged in!")
            st.write("User Information:")
            st.json(user_info)
        else:
            st.error(f"Failed to fetch user information: {response.status_code}")
    except Exception as e:
        st.error(f"An error occurred while fetching user information: {e}")