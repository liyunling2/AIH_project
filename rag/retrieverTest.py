def get_rag_response(query: str, profile: dict, history: list[dict]) -> str:
    return (
        f"**[Mock response]**\n\n"
        f"Hi {profile['name']}! You asked: _{query}_\n\n"
        f"Profile received: role={profile['role']}, "
        f"language={profile['language']}, topic={profile['topic']}\n\n"
        f"Replace this file with the real retriever.py once your API key is ready."
    )