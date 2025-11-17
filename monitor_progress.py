#!/usr/bin/env python3
"""
Monitor processing progress in real-time
"""
import sqlite3
import time
import os

DB_PATH = 'sermons.db'

def get_stats():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM sermons")
    total_sermons = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM sermons WHERE LENGTH(transcript) > 100")
    with_transcripts = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM chunks")
    total_chunks = c.fetchone()[0]
    
    conn.close()
    return total_sermons, with_transcripts, total_chunks

print("Monitoring database changes (press Ctrl+C to stop)...\n")
prev_stats = None

try:
    while True:
        stats = get_stats()
        if stats != prev_stats:
            total, with_trans, chunks = stats
            print(f"[{time.strftime('%H:%M:%S')}] Sermons: {total} | With transcripts: {with_trans} | Chunks: {chunks}")
            prev_stats = stats
        time.sleep(5)
except KeyboardInterrupt:
    print("\nMonitoring stopped.")
