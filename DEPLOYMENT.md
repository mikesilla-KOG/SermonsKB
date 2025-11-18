# SermonsKB - Streamlit Cloud Deployment

## Files included for deployment:
- sermons.db (53.67 MB) - SQLite database with 636 sermon transcripts
- faiss_index.faiss (11.34 MB) - FAISS vector index for semantic search
- embeddings_meta.json (0.35 MB) - Metadata for embeddings

## Setup in Streamlit Cloud:

1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click "New app"
4. Select:
   - Repository: mikesilla-KOG/SermonsKB
   - Branch: main
   - Main file path: app/streamlit_app.py

5. Click "Advanced settings"
6. Add secrets:
   ```
   OPENAI_API_KEY = "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"
   ```

7. Click "Deploy"

## Features:
- 636 sermon transcripts (93.7% of channel)
- Keyword search (FTS5)
- Semantic search (FAISS)
- AI Chat with citations (OpenAI GPT-4)

## Note:
Database files are committed to the repository for easy deployment.
