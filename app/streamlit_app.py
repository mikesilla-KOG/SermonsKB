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

tab = st.sidebar.radio('Mode', ['Keyword Search', 'Semantic Search', 'AI Chat'])

def keyword_search(q, limit=10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT video_id, title, published_at, snippet(sermons, -1, '<b>', '</b>', '...', 100) FROM sermons WHERE sermons MATCH ? LIMIT ?;", (q, limit))
    return cur.fetchall()

if tab == 'Keyword Search':
    q = st.text_input('Search')
    limit = st.slider('Results', 1, 50, 10)
    if q and q.strip():
        rows = keyword_search(q, limit)
        st.write(f'Found {len(rows)} results')
        for vid, title, pub, snippet in rows:
            st.markdown(f'**{title}** — {pub}')
            st.markdown(snippet, unsafe_allow_html=True)
            st.markdown(f'https://www.youtube.com/watch?v={vid}')

elif tab == 'Semantic Search':
    st.write('Semantic Search (requires embeddings index)')
    import numpy as np
    import faiss
    from sentence_transformers import SentenceTransformer

    query = st.text_input('Enter a search phrase')
    top_k = st.slider('Top K', 1, 20, 5)
    if query:
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

else:  # AI Chat
    st.write('💬 Ask questions about the sermons and get AI-powered answers')
    
    if not OPENAI_API_KEY:
        st.error('⚠️ OPENAI_API_KEY not set in .env file. AI Chat requires OpenAI API access.')
    else:
        query = st.text_input('Ask a question:')
        top_k = st.slider('Context chunks', 3, 10, 5)
        
        if query:
            with st.spinner('🔍 Searching sermons and generating answer...'):
                import numpy as np
                import faiss
                from sentence_transformers import SentenceTransformer
                
                # Semantic search to find relevant chunks
                model = SentenceTransformer('all-MiniLM-L6-v2')
                qvec = model.encode([query])[0].astype('float32')
                
                if not os.path.exists(FAISS_INDEX_PATH) or not os.path.exists(EMBEDDINGS_META):
                    st.error('FAISS index not found. Run scripts/build_embeddings.py')
                else:
                    index = faiss.read_index(FAISS_INDEX_PATH)
                    D, I = index.search(np.array([qvec]), top_k)
                    
                    with open(EMBEDDINGS_META, 'r') as f:
                        meta = json.load(f)
                    
                    conn = sqlite3.connect(DB_PATH)
                    cur = conn.cursor()
                    
                    # Collect context from top chunks
                    contexts = []
                    sources = []
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
                        
                        contexts.append(chunk_text)
                        sources.append((title, pub, video_id, chunk_text[:200]))
                    
                    # Generate answer using OpenAI
                    context = "\n\n".join(contexts)
                    prompt = f"""You are a helpful assistant that answers questions based on sermon transcripts. 
Use the following sermon excerpts to answer the question. Be thorough and helpful, citing specific points from the sermons when relevant.
If the sermons don't contain relevant information, say so honestly.

Sermon Context:
{context}

Question: {query}

Answer:"""
                    
                    import requests
                    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
                    data = {
                        "model": "gpt-4o-mini", 
                        "messages": [{"role": "user", "content": prompt}], 
                        "max_tokens": 800,
                        "temperature": 0.7
                    }
                    r = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
                    
                    if r.status_code == 200:
                        ans = r.json()['choices'][0]['message']['content']
                        
                        st.markdown('### 🤖 Answer:')
                        st.markdown(ans)
                        
                        st.markdown('---')
                        st.markdown('### 📚 Sources:')
                        for title, pub, vid, preview in sources:
                            with st.expander(f"{title} — {pub}"):
                                st.write(preview + "...")
                                st.markdown(f'[Watch on YouTube](https://www.youtube.com/watch?v={vid})')
                    else:
                        st.error(f'OpenAI request failed: {r.text}')
