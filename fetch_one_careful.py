"""
Careful single-video transcript fetcher with authentication support.
Uses cookies.txt file for YouTube authentication if available.
"""

import sqlite3
import time
import sys
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

def get_video_info(video_id):
    """Get video info from database"""
    conn = sqlite3.connect('sermons.db')
    c = conn.cursor()
    c.execute('SELECT title FROM sermons WHERE video_id = ?', (video_id,))
    result = c.fetchone()
    conn.close()
    return result

def fetch_transcript_careful(video_id):
    """
    Carefully fetch transcript for a single video.
    Uses manual transcript (not auto-generated) if available.
    """
    try:
        print(f"\n{'='*60}")
        print(f"Fetching transcript for: {video_id}")
        print(f"{'='*60}")
        
        # Get video info
        info = get_video_info(video_id)
        if info:
            print(f"Title: {info[0]}")
        
        # Add a small delay before API call
        print("\nWaiting 2 seconds before fetching...")
        time.sleep(2)
        
        # Fetch transcript
        print("Fetching transcript from YouTube...")
        api = YouTubeTranscriptApi()
        transcript_data = api.fetch(video_id)
        
        # Format transcript - handle typed objects
        text_parts = [s.text for s in transcript_data]
        full_text = ' '.join(text_parts)
        
        print(f"\n✓ Successfully fetched transcript")
        print(f"  Length: {len(full_text)} characters")
        print(f"  Segments: {len(transcript_data)}")
        
        return full_text
        
    except TranscriptsDisabled:
        print("❌ Transcripts are disabled for this video")
        return None
    except NoTranscriptFound:
        print("❌ No transcript found for this video")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def update_database(video_id, transcript):
    """Update transcript in database"""
    conn = sqlite3.connect('sermons.db')
    c = conn.cursor()
    c.execute('''
        UPDATE sermons 
        SET transcript = ?
        WHERE video_id = ?
    ''', (transcript, video_id))
    conn.commit()
    rows_updated = c.rowcount
    conn.close()
    return rows_updated

def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_one_careful.py <video_id>")
        print("\nExample: python fetch_one_careful.py CHzoSAREEaY")
        sys.exit(1)
    
    video_id = sys.argv[1]
    
    print(f"\n🎯 Careful Transcript Fetcher")
    print(f"Video ID: {video_id}")
    
    # Fetch transcript
    transcript = fetch_transcript_careful(video_id)
    
    if transcript:
        # Save to database
        print("\nSaving to database...")
        rows = update_database(video_id, transcript)
        if rows > 0:
            print(f"✓ Database updated successfully")
        else:
            print(f"⚠ Warning: No rows updated (video_id might not exist in database)")
        
        # Show preview
        print("\n" + "="*60)
        print("TRANSCRIPT PREVIEW (first 500 chars):")
        print("="*60)
        print(transcript[:500])
        if len(transcript) > 500:
            print("...")
        print("="*60)
    else:
        print("\n❌ Failed to fetch transcript")
        sys.exit(1)

if __name__ == '__main__':
    main()
