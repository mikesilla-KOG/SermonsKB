"""
Mark videos with disabled transcripts in the database so we don't retry them.
Adds a 'transcript_status' column to track: NULL (not tried), 'available', 'disabled'
"""

import sqlite3

def update_schema():
    """Add transcript_status column if it doesn't exist"""
    conn = sqlite3.connect('sermons.db')
    c = conn.cursor()
    
    # Check if column exists
    c.execute("PRAGMA table_info(sermons)")
    columns = [row[1] for row in c.fetchall()]
    
    if 'transcript_status' not in columns:
        print("Adding 'transcript_status' column to database...")
        c.execute('ALTER TABLE sermons ADD COLUMN transcript_status TEXT')
        
        # Mark existing videos with transcripts as 'available'
        c.execute('''
            UPDATE sermons 
            SET transcript_status = 'available' 
            WHERE transcript IS NOT NULL AND LENGTH(transcript) > 0
        ''')
        
        rows_updated = c.rowcount
        conn.commit()
        print(f"✓ Column added and {rows_updated} existing transcripts marked as 'available'")
    else:
        print("✓ 'transcript_status' column already exists")
    
    conn.close()

def show_status():
    """Show current status breakdown"""
    conn = sqlite3.connect('sermons.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT 
            transcript_status,
            COUNT(*) as count
        FROM sermons
        GROUP BY transcript_status
    ''')
    
    results = c.fetchall()
    
    print("\nCurrent status breakdown:")
    print("=" * 50)
    total = 0
    for status, count in results:
        status_label = status if status else 'not_tried'
        print(f"  {status_label}: {count}")
        total += count
    print(f"  TOTAL: {total}")
    print("=" * 50)
    
    conn.close()

if __name__ == '__main__':
    update_schema()
    show_status()
