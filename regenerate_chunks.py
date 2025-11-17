#!/usr/bin/env python3
"""
Regenerate chunks for all videos that have transcripts but no chunks.
"""
import sqlite3
import os

DB_PATH = 'sermons.db'
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    if not text:
        return []
    chunks = []
    start = 0
    L = len(text)
    max_iterations = (L // (size - overlap)) + 2
    iteration = 0
    while start < L and iteration < max_iterations:
        end = min(start + size, L)
        chunks.append(text[start:end])
        if end >= L:
            break
        start = end - overlap
        iteration += 1
    return chunks

def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get all sermons with transcripts
    c.execute("SELECT video_id, transcript FROM sermons WHERE LENGTH(transcript) > 0")
    sermons_with_transcripts = c.fetchall()
    print(f"Found {len(sermons_with_transcripts)} sermons with transcripts")
    
    # Clear existing chunks
    print("Clearing existing chunks...")
    c.execute("DELETE FROM chunks")
    conn.commit()
    
    # Regenerate chunks
    print("Regenerating chunks...")
    total_chunks = 0
    for video_id, transcript in sermons_with_transcripts:
        chunks = chunk_text(transcript)
        for chunk in chunks:
            c.execute("INSERT INTO chunks(video_id, chunk_text) VALUES (?, ?)", (video_id, chunk))
            total_chunks += 1
        if total_chunks % 100 == 0:
            print(f"  Generated {total_chunks} chunks...")
            conn.commit()
    
    conn.commit()
    print(f"\nDone! Generated {total_chunks} chunks for {len(sermons_with_transcripts)} videos")
    conn.close()

if __name__ == '__main__':
    main()
