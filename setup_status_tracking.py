"""
Create a separate table to track transcript availability status.
This avoids altering the FTS5 virtual table.
"""

import sqlite3

def create_status_table():
    """Create transcript_status tracking table"""
    conn = sqlite3.connect('sermons.db')
    c = conn.cursor()
    
    # Create status tracking table
    c.execute('''
        CREATE TABLE IF NOT EXISTS transcript_status (
            video_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("✓ Created transcript_status table")
    
    # Mark existing videos with transcripts as 'available'
    c.execute('''
        INSERT OR REPLACE INTO transcript_status (video_id, status)
        SELECT video_id, 'available'
        FROM sermons
        WHERE transcript IS NOT NULL AND LENGTH(transcript) > 0
    ''')
    
    rows_inserted = c.rowcount
    conn.commit()
    print(f"✓ Marked {rows_inserted} existing transcripts as 'available'")
    
    conn.close()

def show_status():
    """Show current status breakdown"""
    conn = sqlite3.connect('sermons.db')
    c = conn.cursor()
    
    # Get total videos
    c.execute('SELECT COUNT(*) FROM sermons')
    total_videos = c.fetchone()[0]
    
    # Get status counts
    c.execute('''
        SELECT status, COUNT(*) as count
        FROM transcript_status
        GROUP BY status
    ''')
    
    results = c.fetchall()
    
    print("\nStatus breakdown:")
    print("=" * 50)
    
    status_counts = dict(results)
    available = status_counts.get('available', 0)
    disabled = status_counts.get('disabled', 0)
    not_tried = total_videos - available - disabled
    
    print(f"  Available: {available}")
    print(f"  Disabled: {disabled}")
    print(f"  Not tried yet: {not_tried}")
    print(f"  TOTAL: {total_videos}")
    print("=" * 50)
    
    conn.close()

if __name__ == '__main__':
    create_status_table()
    show_status()
