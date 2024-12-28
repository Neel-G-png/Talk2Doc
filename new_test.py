import streamlit as st
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
import os
import json
import requests
import logging
import openai

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Configuration
CLIENT_SECRETS_FILE = "credentials/client_secrets.json"
SCOPES = ["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "openid"]
REDIRECT_URI = "http://localhost:8501"

# Initialize session state
if "credentials" not in st.session_state:
    st.session_state.credentials = None

if "user_data" not in st.session_state:
    st.session_state.user_data = {"email": None, "notion_secret": None, "notion_page": None}

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

# Placeholder for secure storage (replace this with Firebase integration)
def store_user_credentials(email, notion_secret, notion_page):
    # Simulate secure storage (you'll replace this with Firebase)
    # For example: firebase.firestore().collection('users').add({...})
    with open("user_credentials.json", "w") as file:
        json.dump(
            {"email": email, "notion_secret": notion_secret, "notion_page": notion_page},
            file,
        )

# Chatbot function
def chatbot_interface():
    st.title("Chatbot Interface")
    st.write("Start a conversation with the chatbot below!")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display past messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f"**You**: {message['content']}")
        else:
            st.markdown(f"**Bot**: {message['content']}")

    # Input new message
    user_input = st.text_input("Your message", key="user_input")

    if st.button("Send"):
        if user_input:
            # Append user message
            st.session_state.messages.append({"role": "user", "content": user_input})

            # Generate bot response (placeholder using OpenAI's GPT)
            openai.api_key = "your_openai_api_key_here"  # Replace with your OpenAI API key
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        *st.session_state.messages,
                    ],
                )
                bot_message = response["choices"][0]["message"]["content"]
                st.session_state.messages.append({"role": "assistant", "content": bot_message})
            except Exception as e:
                st.error(f"Error with chatbot response: {e}")

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
            user_email = user_info["email"]
            st.session_state.user_data["email"] = user_email
            st.success(f"Logged in as {user_email}")
            
            # Step 4: Collect Notion credentials
            if not st.session_state.user_data["notion_secret"] or not st.session_state.user_data["notion_page"]:
                st.subheader("Enter Notion Credentials")
                notion_secret = st.text_input("Notion Secret ID", type="password")
                notion_page = st.text_input("Notion Page ID")
                
                if st.button("Save Notion Credentials"):
                    if notion_secret and notion_page:
                        st.session_state.user_data["notion_secret"] = notion_secret
                        st.session_state.user_data["notion_page"] = notion_page
                        store_user_credentials(user_email, notion_secret, notion_page)
                        st.success("Credentials saved successfully!")
                    else:
                        st.error("Please enter both Notion Secret ID and Page ID.")
            else:
                st.success("Your credentials are already saved.")
                chatbot_interface()

        else:
            st.error(f"Failed to fetch user information: {response.status_code}")
    except Exception as e:
        st.error(f"An error occurred while fetching user information: {e}")