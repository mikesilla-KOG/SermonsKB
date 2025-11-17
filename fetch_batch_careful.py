"""
Batch transcript fetcher - processes multiple videos one at a time with delays.
Uses cookies.txt for authentication if available.
"""

import sqlite3
import time
import sys
import os
import requests
from http.cookiejar import MozillaCookieJar
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

def create_session_with_cookies():
    """Create a requests session with cookies from cookies.txt"""
    session = requests.Session()
    cookies_path = 'cookies.txt'
    
    if os.path.exists(cookies_path):
        cookie_jar = MozillaCookieJar(cookies_path)
        cookie_jar.load(ignore_discard=True, ignore_expires=True)
        session.cookies = cookie_jar
        print("✓ Using cookies from cookies.txt for authentication")
    else:
        print("⚠ No cookies.txt found - proceeding without authentication")
    
    return session

def get_videos_needing_transcripts(limit=None):
    """Get list of video IDs that need transcripts"""
    conn = sqlite3.connect('sermons.db')
    c = conn.cursor()
    query = 'SELECT video_id, title FROM sermons WHERE transcript IS NULL OR LENGTH(transcript) = 0'
    if limit:
        query += f' LIMIT {limit}'
    c.execute(query)
    results = c.fetchall()
    conn.close()
    return results

def fetch_transcript(video_id, api):
    """Fetch transcript for a single video"""
    try:
        transcript_data = api.fetch(video_id)
        text_parts = [s.text for s in transcript_data]
        full_text = ' '.join(text_parts)
        return full_text
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def update_database(video_id, transcript):
    """Update transcript in database"""
    conn = sqlite3.connect('sermons.db')
    c = conn.cursor()
    c.execute('UPDATE sermons SET transcript = ? WHERE video_id = ?', (transcript, video_id))
    conn.commit()
    rows_updated = c.rowcount
    conn.close()
    return rows_updated

def main():
    # Get how many to process
    if len(sys.argv) > 1:
        batch_size = int(sys.argv[1])
    else:
        batch_size = 20  # Default batch size (reduced from 10)
    
    # Limit maximum batch size to avoid blocking
    if batch_size > 40:
        print(f"⚠️  Warning: Batch size reduced from {batch_size} to 40 to avoid IP blocking")
        batch_size = 40
    
    print(f"\n🎯 Batch Transcript Fetcher")
    print(f"Processing up to {batch_size} videos")
    print(f"Delay between videos: 10 seconds")
    print("=" * 60)
    
    # Create session with cookies
    session = create_session_with_cookies()
    api = YouTubeTranscriptApi(http_client=session)
    print("=" * 60)
    
    # Get videos needing transcripts
    videos = get_videos_needing_transcripts(batch_size)
    
    if not videos:
        print("\n✓ All videos already have transcripts!")
        return
    
    print(f"\nFound {len(videos)} videos needing transcripts\n")
    
    success_count = 0
    fail_count = 0
    
    for i, (video_id, title) in enumerate(videos, 1):
        print(f"\n[{i}/{len(videos)}] Processing: {video_id}")
        print(f"Title: {title[:70]}...")
        
        # Fetch transcript
        transcript = fetch_transcript(video_id, api)
        
        if transcript:
            # Save to database
            update_database(video_id, transcript)
            print(f"  ✓ Success! {len(transcript)} characters")
            success_count += 1
        else:
            print(f"  ❌ No transcript available")
            fail_count += 1
        
        # Wait before next video (unless it's the last one)
        if i < len(videos):
            print(f"  ⏳ Waiting 10 seconds...")
            time.sleep(10)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"BATCH COMPLETE")
    print(f"  ✓ Successful: {success_count}")
    print(f"  ❌ Failed: {fail_count}")
    print(f"  Total processed: {len(videos)}")
    print("=" * 60)

if __name__ == '__main__':
    main()
