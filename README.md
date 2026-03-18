# AIH_project

https://aihproject-6vvt74vzzhy7unhysjslzh.streamlit.app/

## Project structure

```
rag-chatbot/
├── app.py                  ← Streamlit app (form + chat in one file)
├── rag/
│   ├── ingest.py           ← Document ingestion into ChromaDB
│   └── retriever.py        ← Vector search + Gemini generation
├── documents/              ← Put your PDFs and text files here
│   └── company_handbook.txt
├── ingest_docs.py          ← Run once to load documents
├── requirements.txt
├── .env.example            ← Copy to .env and fill in your API key
├── .streamlit/
│   └── config.toml         ← Theme settings
└── Dockerfile              ← For Cloud Run deployment
```


