# AIH_project

https://aihproject-6vvt74vzzhy7unhysjslzh.streamlit.app/

## Project structure

```
rag-chatbot/
├── app.py                  ← Streamlit app interface
├── rag/
│   ├── ingest.py           ← Document ingestion into DB (KIV)
│   └── retriever.py        ← Link to Gemini agent
└── requirements.txt
```

## Environment variables

| Variable         | Description                                      |
|------------------|--------------------------------------------------|
| `GOOGLE_API_KEY` | Google AI Studio API key (required)              |

### Run the app

```bash
streamlit run app.py
```

Open http://localhost:8501 — you'll see the onboarding form first, then the chatbot.