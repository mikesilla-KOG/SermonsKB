"""
Find videos that actually have transcripts available by testing them.
This helps us skip videos with disabled transcripts.
"""

import sqlite3
import time
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

def check_transcript_available(video_id):
    """Check if a video has transcripts available without fetching full content"""
    try:
        api = YouTubeTranscriptApi()
        # Just list available transcripts - much faster than fetching
        transcripts = api.list_transcripts(video_id)
        # If we get here, transcripts exist
        return True
    except (TranscriptsDisabled, NoTranscriptFound):
        return False
    except Exception as e:
        error_msg = str(e).lower()
        if 'blocked' in error_msg or 'blocking' in error_msg:
            print(f"\n🚫 IP BLOCKED - stopping search")
            return None  # Signal blocking
        return False

def main():
    conn = sqlite3.connect('sermons.db')
    c = conn.cursor()
    
    # Get videos without transcripts
    c.execute('''
        SELECT video_id, title 
        FROM sermons 
        WHERE transcript IS NULL OR LENGTH(transcript) = 0
        ORDER BY published_at DESC
    ''')
    
    videos = c.fetchall()
    conn.close()
    
    print(f"\n🔍 Checking {len(videos)} videos for transcript availability...")
    print("=" * 70)
    
    available = []
    disabled = []
    
    for i, (video_id, title) in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}] {video_id} - {title[:50]}...")
        
        has_transcript = check_transcript_available(video_id)
        
        if has_transcript is None:
            # IP blocked - stop checking
            break
        elif has_transcript:
            print(f"  ✓ Transcript available")
            available.append((video_id, title))
        else:
            print(f"  ✗ Transcript disabled")
            disabled.append((video_id, title))
        
        # Small delay to avoid rate limiting
        if i < len(videos):
            time.sleep(2)
    
    # Summary
    print("\n" + "=" * 70)
    print(f"\n📊 SUMMARY:")
    print(f"  ✓ Available: {len(available)}")
    print(f"  ✗ Disabled: {len(disabled)}")
    print(f"  Total checked: {len(available) + len(disabled)}")
    
    if available:
        print(f"\n✅ Found {len(available)} videos with transcripts available!")
        print("\nFirst 10 videos ready to fetch:")
        for video_id, title in available[:10]:
            print(f"  • {video_id} - {title[:60]}")
    else:
        print("\n⚠️  No videos with available transcripts found in this batch")

if __name__ == '__main__':
    main()
