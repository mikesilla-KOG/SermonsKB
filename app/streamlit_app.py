import os
import sqlite3
import json
from dotenv import load_dotenv
load_dotenv()
import streamlit as st

# Page config
st.set_page_config(
    page_title="SermonsKB - AI-Powered Sermon Search",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Check if running in embed mode
query_params = st.query_params
is_embedded = query_params.get("embed") == "true"

# Custom CSS with embed mode support
embed_css = """
    <style>
    /* Hide Streamlit branding and UI chrome in embed mode */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Hide sidebar in embed mode */
    [data-testid="stSidebar"] {display: none;}
    
    /* Reduce padding in embed mode */
    .main > div {
        padding-top: 2rem;
    }
    </style>
""" if is_embedded else ""

st.markdown(embed_css + """
    <style>
    .main {
        background: linear-gradient(to bottom, #f8f9fa 0%, #ffffff 100%);
    }
    .stTextInput > div > div > input {
        font-size: 18px;
        border-radius: 10px;
        border: 2px solid #e0e0e0;
        padding: 12px;
    }
    .stTextInput > div > div > input:focus {
        border-color: #4CAF50;
        box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
    }
    .answer-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        font-size: 16px;
        line-height: 1.6;
    }
    .source-box {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        margin: 10px 0;
        border-left: 4px solid #4CAF50;
        box-shadow: 0 4px 8px rgba(0,0,0,0.08);
        transition: transform 0.2s;
    }
    .source-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.12);
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        border: none;
        padding: 12px;
        border-radius: 10px;
        font-size: 16px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .stats-box {
        background: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.08);
    }
    .search-result {
        background: white;
        padding: 20px;
        border-radius: 12px;
        margin: 15px 0;
        border-left: 4px solid #2196F3;
        box-shadow: 0 4px 8px rgba(0,0,0,0.08);
    }
    .search-result:hover {
        box-shadow: 0 6px 12px rgba(0,0,0,0.12);
    }
    h1 {
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    </style>
""", unsafe_allow_html=True)

DB_PATH = os.getenv('DB_PATH', 'sermons.db')
FAISS_INDEX_PATH = os.getenv('FAISS_INDEX_PATH', 'faiss_index.faiss')
EMBEDDINGS_META = os.getenv('EMBEDDINGS_META', 'embeddings_meta.json')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Header
st.markdown("<h1 style='text-align: center; font-size: 3.5em; margin-bottom: 10px;'>📖 SermonsKB</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #6c757d; font-size: 20px; margin-bottom: 30px;'>Discover Biblical Wisdom Through AI-Powered Search</p>", unsafe_allow_html=True)

# Mode selector - show in main area if embedded, otherwise in sidebar
if is_embedded:
    st.markdown("### 🔍 Search Mode")
    tab = st.radio('Search Mode', ['AI Chat', 'Semantic Search', 'Keyword Search'], horizontal=True, label_visibility="collapsed")
    st.markdown("---")
else:
    # Sidebar
    with st.sidebar:
        st.markdown("### 🔍 Search Mode")
        tab = st.radio('Search Mode', ['AI Chat', 'Semantic Search', 'Keyword Search'], label_visibility="collapsed")
        
        st.markdown("---")
        st.markdown("### 📊 Statistics")
        
        # Get stats
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM sermons')
        total = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM sermons WHERE transcript IS NOT NULL AND LENGTH(transcript) > 0')
        with_transcripts = c.fetchone()[0]
        conn.close()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Videos", total)
        with col2:
            st.metric("With Transcripts", with_transcripts)
        
        st.progress(with_transcripts / total if total > 0 else 0)
        st.caption(f"{(with_transcripts/total*100):.1f}% Complete")
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.caption("Search through 636+ sermon transcripts using AI-powered semantic search and get intelligent answers to your questions.")
        st.caption("Built with Streamlit, OpenAI, and FAISS.")

def keyword_search(q, limit=10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT video_id, title, published_at, snippet(sermons, -1, '<b>', '</b>', '...', 100) FROM sermons WHERE sermons MATCH ? LIMIT ?;", (q, limit))
    return cur.fetchall()

if tab == 'Keyword Search':
    st.markdown("### 🔎 Keyword Search")
    st.caption("Fast full-text search across all sermon transcripts")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        q = st.text_input('Search keywords:', placeholder="e.g., faith, grace, salvation")
    with col2:
        limit = st.number_input('Results', 1, 50, 10, label_visibility="collapsed")
    
    if q and q.strip():
        rows = keyword_search(q, limit)
        st.success(f'✨ Found {len(rows)} results')
        
        for vid, title, pub, snippet in rows:
            st.markdown(f'''
                <div class="search-result">
                    <h4 style="margin: 0 0 10px 0; color: #2c3e50;">{title}</h4>
                    <p style="color: #6c757d; font-size: 14px; margin: 0 0 10px 0;">📅 {pub}</p>
                    <div style="margin: 10px 0;">{snippet}</div>
                    <a href="https://www.youtube.com/watch?v={vid}" target="_blank" style="color: #667eea; text-decoration: none; font-weight: 500;">🎥 Watch on YouTube →</a>
                </div>
            ''', unsafe_allow_html=True)

elif tab == 'Semantic Search':
    st.markdown("### 🧠 Semantic Search")
    st.caption("Find sermons by meaning, not just keywords")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input('Describe what you\'re looking for:', placeholder="e.g., overcoming challenges with faith")
    with col2:
        top_k = st.number_input('Results', 1, 20, 5, label_visibility="collapsed")
    
    if query:
        with st.spinner('🔍 Searching...'):
            import numpy as np
            import faiss
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer('all-MiniLM-L6-v2')
            qvec = model.encode([query])[0].astype('float32')
            
            if not os.path.exists(FAISS_INDEX_PATH) or not os.path.exists(EMBEDDINGS_META):
                st.error('⚠️ FAISS index not found. Run scripts/build_embeddings.py')
            else:
                index = faiss.read_index(FAISS_INDEX_PATH)
                D, I = index.search(np.array([qvec]), top_k)
                with open(EMBEDDINGS_META, 'r') as f:
                    meta = json.load(f)
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                
                st.success(f'✨ Found {len(I[0])} relevant passages')
                
                for i, idx in enumerate(I[0], 1):
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
                    
                    st.markdown(f'''
                        <div class="search-result">
                            <h4 style="margin: 0 0 10px 0; color: #2c3e50;">{i}. {title}</h4>
                            <p style="color: #6c757d; font-size: 14px; margin: 0 0 15px 0;">📅 {pub}</p>
                            <div style="color: #495057; line-height: 1.6; margin: 15px 0;">{chunk_text[:800]}...</div>
                            <a href="https://www.youtube.com/watch?v={video_id}" target="_blank" style="color: #667eea; text-decoration: none; font-weight: 500;">🎥 Watch on YouTube →</a>
                        </div>
                    ''', unsafe_allow_html=True)

else:  # AI Chat
    st.markdown("### 💬 Ask a Question")
    st.markdown("Ask any question about the sermons and get AI-powered answers with sources.")
    
    if not OPENAI_API_KEY:
        st.error('⚠️ OPENAI_API_KEY not set. AI Chat requires OpenAI API access.')
    else:
        query = st.text_input('Your question:', placeholder="e.g., What does the Bible say about faith and works?")
        
        col1, col2, col3 = st.columns([3, 1, 1])
        with col2:
            top_k = st.slider('Context sources', 3, 10, 5)
        with col3:
            st.write("")  # spacing
            submit = st.button('🔍 Ask', type='primary', use_container_width=True)
        
        if query and submit:
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
                        sources.append((title, pub, video_id, chunk_text[:300]))
                    
                    # Generate answer using OpenAI
                    context = "\n\n".join(contexts)
                    prompt = f"""You are a helpful assistant that answers questions based on sermon transcripts. 
Use the following sermon excerpts to answer the question. Be thorough and helpful, citing specific points from the sermons when relevant.

CRITICAL INSTRUCTION: You MUST include multiple relevant Bible verses to support and reinforce your answer. For each verse:
1. Provide the complete reference (e.g., John 3:16, Romans 8:28, Ephesians 2:8-9)
2. Quote the full verse text
3. Explain how it relates to the sermon content and the question

Include at least 3-5 Bible verses in your response when relevant. Make the Scripture references prominent and easy to identify.

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
                        "max_tokens": 1200,
                        "temperature": 0.7
                    }
                    r = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
                    
                    if r.status_code == 200:
                        ans = r.json()['choices'][0]['message']['content']
                        
                        # Display answer in a nice box
                        st.markdown("### 🤖 Answer")
                        st.markdown(f'<div class="answer-box">{ans}</div>', unsafe_allow_html=True)
                        
                        st.markdown("---")
                        st.markdown("### 📚 Source Sermons")
                        st.caption(f"Found {len(sources)} relevant sermon excerpts")
                        
                        for i, (title, pub, vid, preview) in enumerate(sources, 1):
                            with st.expander(f"📖 {i}. {title} ({pub})"):
                                st.write(preview + "...")
                                st.markdown(f'[🎥 Watch on YouTube](https://www.youtube.com/watch?v={vid})')
                    else:
                        st.error(f'❌ OpenAI request failed: {r.text}')
