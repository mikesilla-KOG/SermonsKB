"""
Rebuild chunks table from existing transcripts in the database.
Run this after fetching many new transcripts to update the chunks for semantic search.
"""

import sqlite3
import re

DB_PATH = 'sermons.db'
CHUNK_SIZE = 500  # words per chunk
OVERLAP = 50      # words overlap between chunks

def create_chunks_table():
    """Create or recreate chunks table"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Drop and recreate to ensure fresh data
    c.execute('DROP TABLE IF EXISTS chunks')
    c.execute('''
        CREATE TABLE chunks (
            chunk_id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            chunk_text TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ Created chunks table")

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    """Split text into overlapping chunks by word count"""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        if i + chunk_size >= len(words):
            break
    
    return chunks

def rebuild_chunks():
    """Rebuild all chunks from transcripts"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get all videos with transcripts
    c.execute('''
        SELECT video_id, transcript 
        FROM sermons 
        WHERE transcript IS NOT NULL AND LENGTH(transcript) > 0
    ''')
    
    videos = c.fetchall()
    print(f"\nProcessing {len(videos)} videos with transcripts...")
    
    total_chunks = 0
    for i, (video_id, transcript) in enumerate(videos, 1):
        if not transcript or len(transcript.strip()) == 0:
            continue
        
        # Create chunks for this video
        chunks = chunk_text(transcript)
        
        # Insert chunks
        for chunk in chunks:
            c.execute('INSERT INTO chunks (video_id, chunk_text) VALUES (?, ?)', 
                     (video_id, chunk))
        
        total_chunks += len(chunks)
        
        if i % 50 == 0:
            print(f"  Processed {i}/{len(videos)} videos, {total_chunks} chunks so far...")
            conn.commit()
    
    conn.commit()
    conn.close()
    
    print(f"\n✓ Created {total_chunks} chunks from {len(videos)} videos")
    return total_chunks

def main():
    print("Rebuilding chunks from transcripts...")
    print("=" * 60)
    
    create_chunks_table()
    total = rebuild_chunks()
    
    print("\n" + "=" * 60)
    print(f"Done! Ready to rebuild embeddings with {total} chunks")
    print("Next step: python scripts/build_embeddings.py")

if __name__ == '__main__':
    main()
