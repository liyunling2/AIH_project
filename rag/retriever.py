# rag/retriever.py  —  FINAL VERSION
import uuid
import streamlit as st
from google.oauth2 import service_account
from google.cloud.dialogflowcx_v3 import (
    SessionsClient,
    QueryInput,
    TextInput,
    DetectIntentRequest,
)

# Read config from Streamlit secrets
PROJECT_ID = st.secrets["GOOGLE_CLOUD_PROJECT"]
LOCATION   = st.secrets.get("GOOGLE_LOCATION", "us-central1")
AGENT_ID   = st.secrets["AGENT_ENGINE_ID"]

# Build credentials from the service account in Streamlit secrets
creds = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)

# Dialogflow CX client pointing at your agent's region
_client = SessionsClient(
    credentials=creds,
    client_options={"api_endpoint": f"{LOCATION}-dialogflow.googleapis.com"},
)


def get_rag_response(query: str, profile: dict, history: list[dict]) -> str:
    # Consistent session ID per user so the agent remembers context
    session_id = str(uuid.uuid5(
        uuid.NAMESPACE_DNS,
        profile["name"].lower().replace(" ", "-")
    ))

    session_path = _client.session_path(
        project=PROJECT_ID,
        location=LOCATION,
        agent=AGENT_ID,
        session=session_id,
    )

    # Inject form profile into the message
    personalised_message = (
        f"[Context: name={profile['name']}, rental_stage={profile['rental_stage']}, user_role={profile['user_role']}, property_type={profile['property_type']},"
        f"language={profile['language']}, ageGroup={profile['ageGroup']}]\n\n"
        f"{query}\n\n"
        f"Please respond in {profile['language']}."
    )

    request = DetectIntentRequest(
        session=session_path,
        query_input=QueryInput(
            text=TextInput(text=personalised_message),
            language_code="en",
        ),
    )

    try:
        response = _client.detect_intent(request=request)

        reply_parts = []
        for message in response.query_result.response_messages:
            if message.text.text:
                reply_parts.extend(message.text.text)

        return "\n".join(reply_parts) if reply_parts else "I could not find an answer."

    except Exception as e:
        return f"Error calling agent: {str(e)}"
