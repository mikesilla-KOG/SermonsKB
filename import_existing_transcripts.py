#!/usr/bin/env python3
"""
Import existing transcript JSON files into the SQLite database.

This script reads all the JSON transcript files from data/transcripts/ 
and imports them into the sermons.db database, creating chunks for embedding.
"""

import os
import json
import sqlite3
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv('DB_PATH', 'sermons.db')
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS sermons USING fts5(video_id, title, published_at, transcript);")
    c.execute("CREATE TABLE IF NOT EXISTS chunks(chunk_id INTEGER PRIMARY KEY AUTOINCREMENT, video_id TEXT, chunk_text TEXT);")
    conn.commit()
    return conn

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    if not text or not text.strip():
        return []
    
    chunks = []
    start = 0
    L = len(text)
    
    while start < L:
        end = min(start + size, L)
        chunk = text[start:end].strip()
        if chunk:  # Only add non-empty chunks
            chunks.append(chunk)
        start = end - overlap
        if start < 0:
            start = 0
        if start >= L:
            break
    return chunks

def insert_into_db(conn, video_id, title, published_at, transcript):
    c = conn.cursor()
    
    # Check if already exists
    c.execute("SELECT rowid FROM sermons WHERE video_id = ?", (video_id,))
    if c.fetchone():
        print(f"Skipping {video_id} - already exists in database")
        return
    
    c.execute("INSERT INTO sermons(video_id, title, published_at, transcript) VALUES (?, ?, ?, ?)",
              (video_id, title, published_at, transcript))
    
    # Create chunks if we have transcript content
    if transcript and transcript.strip():
        chunks = chunk_text(transcript)
        for chunk in chunks:
            c.execute("INSERT INTO chunks(video_id, chunk_text) VALUES (?, ?)", (video_id, chunk))
        print(f"Imported {video_id}: {len(chunks)} chunks")
    else:
        print(f"Imported {video_id}: no transcript content")
    
    conn.commit()

def main():
    conn = ensure_db()
    transcript_dir = 'data/transcripts'
    
    if not os.path.exists(transcript_dir):
        print(f"Transcript directory {transcript_dir} not found!")
        return
    
    # Get all JSON files
    json_files = [f for f in os.listdir(transcript_dir) if f.endswith('.json')]
    
    if not json_files:
        print("No JSON transcript files found!")
        return
    
    print(f"Found {len(json_files)} transcript files to import...")
    
    imported_count = 0
    chunks_count = 0
    
    for filename in tqdm(json_files, desc="Importing transcripts"):
        try:
            filepath = os.path.join(transcript_dir, filename)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            video_id = data.get('video_id', filename.replace('.json', ''))
            title = data.get('title', '')
            published_at = data.get('published_at', data.get('upload_date', ''))
            transcript = data.get('transcript', '')
            
            # Skip if transcript is empty or too short
            if not transcript or len(transcript.strip()) < 10:
                continue
                
            insert_into_db(conn, video_id, title, published_at, transcript)
            imported_count += 1
            
            # Count chunks for this video
            if transcript and transcript.strip():
                chunks_count += len(chunk_text(transcript))
                
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            continue
    
    print(f"\nImport complete!")
    print(f"Imported {imported_count} transcripts with content")
    print(f"Created approximately {chunks_count} text chunks")
    
    # Show final database stats
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sermons")
    sermon_count = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM chunks")
    chunk_count = c.fetchone()[0]
    
    print(f"Database now contains:")
    print(f"  - {sermon_count} sermons")
    print(f"  - {chunk_count} chunks ready for embedding")

if __name__ == '__main__':
    main()