# rag/retriever.py  —  Vertex AI Agent Engine version
import os
import vertexai
from vertexai import agent_engines
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID      = os.environ["GOOGLE_CLOUD_PROJECT"]  
LOCATION        = os.environ.get("GOOGLE_LOCATION", "us-central1")
AGENT_ENGINE_ID = os.environ["AGENT_ENGINE_ID"]        # the number from the URL

# Initialise the Vertex AI client once at import time
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Reference to your deployed agent (no code deployment needed — it's already live)
_agent = agent_engines.get(AGENT_ENGINE_ID)


def get_rag_response(query: str, profile: dict, history: list[dict]) -> str:
    """
    Send a message to the deployed Vertex AI agent and return its reply.
    Profile data from the onboarding form is prepended to the query so the
    agent knows who it's talking to.
    """

    # Inject profile context into the message — the agent sees this as part
    # of the user's question, so it personalises the response accordingly
    personalised_query = f"""[User context: name={profile['name']}, 
    role={profile['role']}, language={profile['language']}, 
    topic={profile['topic']}]

    {query}

    Please respond in {profile['language']}."""

    # Create or reuse a session keyed to this user's name (keeps history)
    session_id = f"session-{profile['name'].lower().replace(' ', '-')}"

    try:
        stream = _agent.stream_query(
        message=personalised_query,
        session_id=session_id,
        )

        full_response = ""
        for event in stream:
            parts = event.get("content", {}).get("parts", [])
            for part in parts:
                if "text" in part:
                    full_response += part["text"]

        return full_response.strip() if full_response else "I could not find an answer in the documents."

    except Exception as e:
        return f"Error calling agent: {str(e)}"