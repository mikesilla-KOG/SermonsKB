"""Check a sample of videos to see their transcript status"""
import sqlite3

conn = sqlite3.connect('sermons.db')
c = conn.cursor()

# Check recent videos
c.execute('''
    SELECT video_id, title, 
           CASE WHEN transcript IS NULL THEN 0 
                WHEN LENGTH(transcript) = 0 THEN 0 
                ELSE 1 END as has_transcript
    FROM sermons 
    ORDER BY published_at DESC 
    LIMIT 30
''')

results = c.fetchall()

print("\nRecent videos (newest first):")
print("=" * 80)
for video_id, title, has_transcript in results:
    status = "✓" if has_transcript else "✗"
    print(f"{status} {video_id} - {title[:60]}")

# Check videos without transcripts
c.execute('''
    SELECT video_id, title
    FROM sermons 
    WHERE transcript IS NULL OR LENGTH(transcript) = 0
    ORDER BY published_at DESC
    LIMIT 10
''')

print("\n\nVideos needing transcripts (newest first):")
print("=" * 80)
for video_id, title in c.fetchall():
    print(f"{video_id} - {title[:60]}")

conn.close()
