#!/usr/bin/env python3
"""
Rebuild database from transcripts that have embeddings
"""
import sqlite3
import json
import os

def main():
    # Get the video IDs that have embeddings 
    with open('embeddings_meta.json', 'r') as f:
        meta = json.load(f)

    embedded_videos = set()
    for item in meta:
        embedded_videos.add(item['video_id'])

    print(f'Found {len(embedded_videos)} videos with embeddings')
    
    # Setup database
    conn = sqlite3.connect('sermons.db')
    c = conn.cursor()
    c.execute('CREATE VIRTUAL TABLE IF NOT EXISTS sermons USING fts5(video_id, title, published_at, transcript);')
    c.execute('CREATE TABLE IF NOT EXISTS chunks(chunk_id INTEGER PRIMARY KEY AUTOINCREMENT, video_id TEXT, chunk_text TEXT);')
    conn.commit()

    # Import the transcripts that have embeddings
    imported = 0
    for video_id in embedded_videos:
        try:
            transcript_file = f'data/transcripts/{video_id}.json'
            if os.path.exists(transcript_file):
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                title = data.get('title', '')
                published_at = data.get('published_at', '')
                transcript = data.get('transcript', '')
                
                if transcript and len(transcript) > 100:
                    # Check if already exists
                    c.execute('SELECT rowid FROM sermons WHERE video_id = ?', (video_id,))
                    if not c.fetchone():
                        c.execute('INSERT INTO sermons(video_id, title, published_at, transcript) VALUES (?, ?, ?, ?)',
                                  (video_id, title, published_at, transcript))
                        imported += 1
        except Exception as e:
            print(f'Error with {video_id}: {e}')

    conn.commit()
    print(f'Imported {imported} sermons')

    # Check final counts
    c.execute('SELECT COUNT(*) FROM sermons')
    sermon_count = c.fetchone()[0]
    print(f'Database now has {sermon_count} sermons')

if __name__ == '__main__':
    main()