#!/usr/bin/env python3
"""
Import existing transcript files that have actual content into the database
"""
import os
import json
import sqlite3
from pathlib import Path

DB_PATH = 'sermons.db'
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
    if not text or len(text.strip()) < 10:
        return []
    chunks = []
    start = 0
    L = len(text)
    while start < L:
        end = min(start + size, L)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
        if start >= L:
            break
    return chunks

def insert_into_db(conn, video_id, title, published_at, transcript):
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO sermons(video_id, title, published_at, transcript) VALUES (?, ?, ?, ?)",
              (video_id, title, published_at, transcript))
    
    # Delete old chunks and create new ones
    c.execute("DELETE FROM chunks WHERE video_id = ?", (video_id,))
    if transcript and transcript.strip():
        chunks = chunk_text(transcript)
        for chunk in chunks:
            c.execute("INSERT INTO chunks(video_id, chunk_text) VALUES (?, ?)", (video_id, chunk))
    
    conn.commit()
    return len(chunk_text(transcript)) if transcript else 0

def main():
    conn = ensure_db()
    transcript_dir = Path('data/transcripts')
    
    if not transcript_dir.exists():
        print("Transcript directory not found!")
        return
    
    # Find files with substantial content (>1KB = likely has actual transcript)
    files_with_content = []
    for json_file in transcript_dir.glob('*.json'):
        if json_file.stat().st_size > 1000:  # Files > 1KB
            files_with_content.append(json_file)
    
    print(f"Found {len(files_with_content)} files with substantial content")
    
    imported_count = 0
    total_chunks = 0
    
    for json_file in files_with_content:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            video_id = data.get('video_id', json_file.stem)
            title = data.get('title', '')
            published_at = data.get('published_at', data.get('upload_date', ''))
            transcript = data.get('transcript', '')
            
            # Only import if we have actual content
            if transcript and len(transcript.strip()) > 100:
                chunks_created = insert_into_db(conn, video_id, title, published_at, transcript)
                total_chunks += chunks_created
                imported_count += 1
                print(f"Imported {video_id}: {len(transcript)} chars, {chunks_created} chunks")
            
        except Exception as e:
            print(f"Error processing {json_file}: {e}")
    
    print(f"\n=== Import Summary ===")
    print(f"Files processed: {len(files_with_content)}")
    print(f"Successfully imported: {imported_count}")
    print(f"Total chunks created: {total_chunks}")
    
    # Final database stats
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM sermons")
    total_sermons = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM chunks")
    total_db_chunks = c.fetchone()[0]
    
    print(f"\nDatabase now contains:")
    print(f"  Sermons: {total_sermons}")
    print(f"  Chunks: {total_db_chunks}")

if __name__ == '__main__':
    main()