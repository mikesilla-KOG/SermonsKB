#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('sermons.db')
c = conn.cursor()

# Get a recent video that should have a transcript
c.execute("SELECT video_id, LENGTH(transcript), transcript[:100] FROM sermons WHERE video_id = 'M8sc01mZA4U'")
result = c.fetchone()
print(f"Video ID: {result[0]}")
print(f"Transcript length: {result[1]}")
print(f"Transcript preview: {result[2]}")

# Check if it has chunks
c.execute("SELECT COUNT(*) FROM chunks WHERE video_id = 'M8sc01mZA4U'")
print(f"Chunks count: {c.fetchone()[0]}")

conn.close()
