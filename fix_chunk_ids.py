#!/usr/bin/env python3

import sqlite3
import json
import os

def fix_chunk_ids():
    """Fix chunk IDs to match embeddings_meta.json"""
    
    # Load embeddings metadata to get the correct chunk IDs
    with open('embeddings_meta.json', 'r') as f:
        embeddings_meta = json.load(f)
    
    print(f"Loaded {len(embeddings_meta)} chunks from embeddings_meta.json")
    
    # Create a mapping from video_id to chunk metadata
    video_chunks = {}
    for meta in embeddings_meta:
        video_id = meta['video_id']
        if video_id not in video_chunks:
            video_chunks[video_id] = []
        video_chunks[video_id].append(meta)
    
    # Sort each video's chunks by chunk_id to maintain order
    for video_id in video_chunks:
        video_chunks[video_id].sort(key=lambda x: x['chunk_id'])
    
    print(f"Found chunks for {len(video_chunks)} videos")
    
    # Connect to database
    conn = sqlite3.connect('sermons.db')
    cursor = conn.cursor()
    
    # Drop and recreate chunks table
    cursor.execute('DROP TABLE IF EXISTS chunks')
    cursor.execute('''
        CREATE TABLE chunks (
            chunk_id INTEGER PRIMARY KEY,
            video_id TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (video_id) REFERENCES sermons(video_id)
        )
    ''')
    
    total_inserted = 0
    
    # Process each video that has both transcript data and embeddings
    for video_id in video_chunks:
        transcript_file = f'data/transcripts/{video_id}.json'
        if not os.path.exists(transcript_file):
            print(f"Warning: No transcript file for {video_id}")
            continue
            
        # Load transcript
        with open(transcript_file, 'r') as f:
            transcript_data = json.load(f)
        
        if 'transcript' not in transcript_data or not transcript_data['transcript']:
            print(f"Warning: No transcript data in {video_id}")
            continue
        
        # Get full text
        full_text = transcript_data['transcript']
        
        if len(full_text.strip()) == 0:
            print(f"Warning: Empty text for {video_id}")
            continue
        
        # Get chunk metadata for this video
        chunks_meta = video_chunks[video_id]
        
        # Create chunks with the same chunking parameters (1000 chars, 200 overlap)
        chunk_size = 1000
        chunk_overlap = 200
        chunks = []
        
        for i in range(0, len(full_text), chunk_size - chunk_overlap):
            chunk_text = full_text[i:i + chunk_size]
            if len(chunk_text.strip()) > 0:
                chunks.append(chunk_text.strip())
        
        # Match chunks with their original chunk IDs from embeddings
        if len(chunks) != len(chunks_meta):
            print(f"Warning: Chunk count mismatch for {video_id}: generated {len(chunks)}, expected {len(chunks_meta)}")
            # Try to proceed anyway, matching what we can
        
        # Insert chunks with original chunk IDs
        for j, chunk_meta in enumerate(chunks_meta):
            if j < len(chunks):
                chunk_id = chunk_meta['chunk_id']
                chunk_text = chunks[j]
                
                cursor.execute('''
                    INSERT INTO chunks (chunk_id, video_id, content)
                    VALUES (?, ?, ?)
                ''', (chunk_id, video_id, chunk_text))
                total_inserted += 1
        
        print(f"Processed {video_id}: {len(chunks_meta)} chunks")
    
    conn.commit()
    conn.close()
    
    print(f"\nDone! Inserted {total_inserted} chunks with original chunk IDs")
    
    # Verify the fix
    conn = sqlite3.connect('sermons.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT MIN(chunk_id), MAX(chunk_id), COUNT(*) FROM chunks')
    min_id, max_id, count = cursor.fetchone()
    print(f"Chunk IDs now range from {min_id} to {max_id} with {count} total chunks")
    
    # Test the specific chunk IDs that were failing
    test_ids = [758, 713, 1063]
    for chunk_id in test_ids:
        cursor.execute('SELECT video_id, content FROM chunks WHERE chunk_id = ?', (chunk_id,))
        result = cursor.fetchone()
        if result:
            print(f"✅ Chunk {chunk_id} found: video_id={result[0]}, content length={len(result[1])}")
        else:
            print(f"❌ Chunk {chunk_id} still not found")
    
    conn.close()

if __name__ == '__main__':
    fix_chunk_ids()