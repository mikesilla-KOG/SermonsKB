# SermonsKB

This project builds a searchable knowledge base (KB) of sermon transcripts from a YouTube channel.

What the scaffold includes:
- `scripts/fetch_and_store.py` — list videos, fetch transcripts, optional OpenAI transcription fallback, store in `sermons.db` (FTS + chunks).
- `scripts/build_embeddings.py` — build embeddings (OpenAI or local `sentence-transformers`) and create a FAISS index.
- `app/streamlit_app.py` — Streamlit app for Keyword Search and Semantic Search / Ask (RAG via OpenAI optional).
- `requirements.txt` — Python dependencies.

Quick start

1. Create & activate a venv and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Fetch and store transcripts (no API keys required for public videos):
```bash
python scripts/fetch_and_store.py <CHANNEL_OR_PLAYLIST_URL>
```

3. Build embeddings and FAISS index (optional, for semantic search):
```bash
# if you want OpenAI embeddings set OPENAI_API_KEY in your environment or .env
python scripts/build_embeddings.py
```

4. Run the Streamlit UI:
```bash
streamlit run app/streamlit_app.py
```

Notes & next steps
- If transcripts are missing, the fetch script will attempt to use OpenAI's transcription API when `OPENAI_API_KEY` is set. If you prefer a local Whisper install, modify `fetch_and_store.py` to call your local transcription tool.
- FAISS and sentence-transformers are used locally by default to avoid paid APIs. You can switch to OpenAI embeddings by setting `OPENAI_API_KEY`.
- Add `.env` to the project root for environment variables; `.gitignore` already excludes secrets and DB files.

If you want, I can run a small test (2–5 videos) from a channel URL you provide, or help set up an OpenAI key for higher-quality transcriptions and embeddings.
