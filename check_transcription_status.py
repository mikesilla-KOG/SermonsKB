"""
Check transcription progress and status
"""
import sqlite3
from datetime import datetime

def get_status():
    conn = sqlite3.connect('sermons.db')
    cursor = conn.cursor()
    
    # Total videos
    cursor.execute('SELECT COUNT(*) FROM sermons')
    total = cursor.fetchone()[0]
    
    # Videos with transcripts
    cursor.execute('SELECT COUNT(*) FROM sermons WHERE length(transcript) > 0')
    completed = cursor.fetchone()[0]
    
    # Videos without transcripts
    cursor.execute('SELECT COUNT(*) FROM sermons WHERE length(transcript) = 0 OR transcript IS NULL')
    remaining = cursor.fetchone()[0]
    
    # Average transcript length
    cursor.execute('SELECT AVG(length(transcript)) FROM sermons WHERE length(transcript) > 0')
    avg_length = cursor.fetchone()[0] or 0
    
    # Recently completed (last 10)
    cursor.execute('''
        SELECT video_id, title, length(transcript) as len 
        FROM sermons 
        WHERE length(transcript) > 0 
        ORDER BY rowid DESC 
        LIMIT 10
    ''')
    recent = cursor.fetchall()
    
    conn.close()
    
    # Calculate progress
    progress_pct = (completed / total * 100) if total > 0 else 0
    
    # Estimate time remaining (assuming 40 seconds per video average)
    est_seconds = remaining * 40
    est_hours = est_seconds / 3600
    est_minutes = (est_seconds % 3600) / 60
    
    print("=" * 70)
    print(f"TRANSCRIPTION STATUS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"\nOverall Progress:")
    print(f"  Total videos:      {total}")
    print(f"  Completed:         {completed} ({progress_pct:.1f}%)")
    print(f"  Remaining:         {remaining}")
    print(f"  Avg transcript:    {avg_length:.0f} characters")
    
    print(f"\nEstimated Time Remaining:")
    print(f"  ~{est_hours:.1f} hours ({est_minutes:.0f} minutes)")
    print(f"  (Based on ~40 seconds per video average)")
    
    if recent:
        print(f"\nRecently Completed (last {len(recent)}):")
        for vid, title, length in recent:
            print(f"  • {vid}: {title[:50]:<50} ({length:,} chars)")
    
    print("\n" + "=" * 70)
    
    # Progress bar
    bar_width = 50
    filled = int(bar_width * completed / total)
    bar = '█' * filled + '░' * (bar_width - filled)
    print(f"[{bar}] {completed}/{total}")
    print("=" * 70)

if __name__ == '__main__':
    get_status()
