import os
import sqlite3
import json
from dotenv import load_dotenv
load_dotenv()
import streamlit as st

DB_PATH = os.getenv('DB_PATH', 'sermons.db')
FAISS_INDEX_PATH = os.getenv('FAISS_INDEX_PATH', 'faiss_index.faiss')
EMBEDDINGS_META = os.getenv('EMBEDDINGS_META', 'embeddings_meta.json')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

st.title('SermonsKB')

tab = st.sidebar.radio('Mode', ['Keyword Search', 'Semantic Search / Ask'])

def keyword_search(q, limit=10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT video_id, title, published_at, snippet(sermons, -1, '<b>', '</b>', '...', 100) FROM sermons WHERE sermons MATCH ? LIMIT ?;", (q, limit))
    return cur.fetchall()

if tab == 'Keyword Search':
    q = st.text_input('Search')
    limit = st.slider('Results', 1, 50, 10)
    if q:
        rows = keyword_search(q, limit)
        st.write(f'Found {len(rows)} results')
        for vid, title, pub, snippet in rows:
            st.markdown(f'**{title}** — {pub}')
            st.markdown(snippet, unsafe_allow_html=True)
            st.markdown(f'https://www.youtube.com/watch?v={vid}')

else:
    st.write('Semantic Search / Ask (requires embeddings index)')
    import numpy as np
    import faiss
    from sentence_transformers import SentenceTransformer

    query = st.text_input('Enter a question or search phrase')
    top_k = st.slider('Top K', 1, 20, 5)
    if query:
        # load model for embeddings (local)
        model = SentenceTransformer('all-MiniLM-L6-v2')
        qvec = model.encode([query])[0].astype('float32')
        if not os.path.exists(FAISS_INDEX_PATH) or not os.path.exists(EMBEDDINGS_META):
            st.error('FAISS index or meta not found. Run scripts/build_embeddings.py')
        else:
            index = faiss.read_index(FAISS_INDEX_PATH)
            D, I = index.search(np.array([qvec]), top_k)
            with open(EMBEDDINGS_META, 'r') as f:
                meta = json.load(f)
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            for idx in I[0]:
                if idx < 0 or idx >= len(meta):
                    continue
                chunk_id = meta[idx]['chunk_id']
                video_id = meta[idx]['video_id']
                cur.execute('SELECT title, published_at FROM sermons WHERE video_id = ? LIMIT 1', (video_id,))
                r = cur.fetchone()
                title = r[0] if r else video_id
                pub = r[1] if r else ''
                cur.execute('SELECT chunk_text FROM chunks WHERE chunk_id = ?', (chunk_id,))
                chunk_text = cur.fetchone()[0]
                st.markdown(f'**{title}** — {pub}')
                st.write(chunk_text[:1000])
                st.markdown(f'https://www.youtube.com/watch?v={video_id}')

        # optional RAG: if OPENAI_API_KEY is present, allow a generated answer
        if OPENAI_API_KEY:
            st.write('You can enable RAG answers (uses OpenAI).')
            if st.button('Generate Answer from Retrieved Context'):
                # collect top texts
                texts = []
                for idx in I[0]:
                    if idx < 0 or idx >= len(meta):
                        continue
                    chunk_id = meta[idx]['chunk_id']
                    video_id = meta[idx]['video_id']
                    cur.execute('SELECT chunk_text FROM chunks WHERE chunk_id = ?', (chunk_id,))
                    chunk_text = cur.fetchone()[0]
                    texts.append(chunk_text)
                context = "\n\n".join(texts[:5])
                prompt = f"Use the following sermon excerpts to answer the question. Be concise.\n\nContext:\n{context}\n\nQuestion: {query}\nAnswer:"
                import requests
                headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
                data = {"model": "gpt-3.5-turbo", "messages": [{"role":"user","content": prompt}], "max_tokens": 256}
                r = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
                if r.status_code == 200:
                    ans = r.json()['choices'][0]['message']['content']
                    st.markdown('**Answer:**')
                    st.write(ans)
                else:
                    st.error('OpenAI request failed: ' + r.text)
