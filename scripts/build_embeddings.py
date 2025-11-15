"""
Build embeddings for transcript chunks and create a FAISS index.

Usage:
  python scripts/build_embeddings.py

Behavior:
 - Reads `chunks` table from `sermons.db`.
 - Computes embeddings using OpenAI if `OPENAI_API_KEY` is set, otherwise uses `sentence-transformers` locally.
 - Builds a FAISS index and saves it to `faiss_index.faiss`.
 - Saves metadata mapping to `embeddings_meta.json`.

Note: Install dependencies from `requirements.txt`. FAISS and large transformer models can be resource-heavy.
"""
import os
import json
import sqlite3
import pickle
from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.getenv('DB_PATH', 'sermons.db')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

EMBEDDINGS_INDEX_PATH = os.getenv('FAISS_INDEX_PATH', 'faiss_index.faiss')
EMBEDDINGS_META = os.getenv('EMBEDDINGS_META', 'embeddings_meta.json')

def get_chunks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT chunk_id, video_id, chunk_text FROM chunks")
    return c.fetchall()

def embed_texts_openai(texts):
    import requests
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    url = "https://api.openai.com/v1/embeddings"
    model = "text-embedding-3-small"
    batch_size = 10
    out = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        data = {"model": model, "input": batch}
        r = requests.post(url, headers=headers, json=data)
        r.raise_for_status()
        j = r.json()
        for item in j['data']:
            out.append(item['embedding'])
    return out

def embed_texts_local(texts):
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    return model.encode(texts, show_progress_bar=True, convert_to_numpy=True).tolist()

def build_faiss(embeddings):
    import faiss
    import numpy as np
    vecs = np.array(embeddings).astype('float32')
    d = vecs.shape[1]
    index = faiss.IndexFlatL2(d)
    index.add(vecs)
    faiss.write_index(index, EMBEDDINGS_INDEX_PATH)

def main():
    rows = get_chunks()
    if not rows:
        print("No chunks found. Run fetch_and_store first.")
        return
    ids = [r[0] for r in rows]
    meta = [{"chunk_id": r[0], "video_id": r[1]} for r in rows]
    texts = [r[2] for r in rows]
    if OPENAI_API_KEY:
        print("Embedding with OpenAI")
        embeddings = embed_texts_openai(texts)
    else:
        print("Embedding with local sentence-transformers")
        embeddings = embed_texts_local(texts)
    build_faiss(embeddings)
    # save meta (in order)
    with open(EMBEDDINGS_META, 'w') as f:
        json.dump(meta, f)
    print("FAISS index and meta saved.")

if __name__ == '__main__':
    main()
