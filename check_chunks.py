#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('sermons.db')
c = conn.cursor()

# Check if chunks table exists
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chunks';")
chunks_table = c.fetchone()
print(f"Chunks table exists: {chunks_table is not None}")

if chunks_table:
    c.execute("SELECT COUNT(*) FROM chunks;")
    chunks_count = c.fetchone()[0]
    print(f"Total chunks: {chunks_count}")
    
    c.execute("SELECT COUNT(DISTINCT video_id) FROM chunks;")
    videos_with_chunks = c.fetchone()[0]
    print(f"Videos with chunks: {videos_with_chunks}")
else:
    print("Chunks table does not exist!")

c.execute("SELECT COUNT(*) FROM sermons;")
sermons_count = c.fetchone()[0]
print(f"Total sermons: {sermons_count}")

conn.close()
