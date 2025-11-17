#!/usr/bin/env python3
"""
Find all videos with empty transcripts and create a list to reprocess.
"""
import sqlite3

DB_PATH = 'sermons.db'

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Find videos with empty or very short transcripts
c.execute("SELECT video_id FROM sermons WHERE LENGTH(transcript) < 100 ORDER BY ROWID")
empty_videos = [row[0] for row in c.fetchall()]

print(f"Found {len(empty_videos)} videos with empty/short transcripts")

# Save to file
with open('videos_to_reprocess.txt', 'w') as f:
    for vid in empty_videos:
        f.write(f"{vid}\n")

print(f"Saved to videos_to_reprocess.txt")
print(f"\nTo reprocess, run:")
print(f"  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass")
print(f"  . .\\.venv\\Scripts\\Activate.ps1")
print(f"  python scripts/fetch_batch.py --ids-file videos_to_reprocess.txt --batch-size 50 --max-videos {len(empty_videos)}")

conn.close()
