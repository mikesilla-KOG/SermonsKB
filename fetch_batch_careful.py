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
    """Get list of video IDs that need transcripts (excluding disabled ones)"""
    conn = sqlite3.connect('sermons.db')
    c = conn.cursor()
    
    # Get videos without transcripts that aren't marked as disabled
    query = '''
        SELECT s.video_id, s.title 
        FROM sermons s
        LEFT JOIN transcript_status ts ON s.video_id = ts.video_id
        WHERE (s.transcript IS NULL OR LENGTH(s.transcript) = 0)
          AND (ts.status IS NULL OR ts.status != 'disabled')
    '''
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
    except KeyboardInterrupt:
        raise  # Allow user to stop the script
    except Exception as e:
        error_msg = str(e).lower()
        if 'blocked' in error_msg or 'blocking' in error_msg:
            print(f"  🚫 IP BLOCKED - stopping batch")
            raise  # Stop if we're blocked
        print(f"  ❌ Error: {e}")
        return None

def update_database(video_id, transcript):
    """Update transcript in database and mark as available"""
    conn = sqlite3.connect('sermons.db')
    c = conn.cursor()
    c.execute('UPDATE sermons SET transcript = ? WHERE video_id = ?', (transcript, video_id))
    
    # Mark as available in status table
    c.execute('''
        INSERT OR REPLACE INTO transcript_status (video_id, status, last_checked)
        VALUES (?, 'available', CURRENT_TIMESTAMP)
    ''', (video_id,))
    
    conn.commit()
    rows_updated = c.rowcount
    conn.close()
    return rows_updated

def mark_as_disabled(video_id):
    """Mark a video as having disabled transcripts so we don't retry it"""
    conn = sqlite3.connect('sermons.db')
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO transcript_status (video_id, status, last_checked)
        VALUES (?, 'disabled', CURRENT_TIMESTAMP)
    ''', (video_id,))
    conn.commit()
    conn.close()

def main():
    # Get how many to process
    if len(sys.argv) > 1:
        batch_size = int(sys.argv[1])
    else:
        batch_size = 20  # Default batch size (reduced from 10)
    
    print(f"\n🎯 Batch Transcript Fetcher")
    print(f"Processing up to {batch_size} videos")
    print(f"Delay between videos: 20 seconds")
    print(f"Strategy: Skip videos without transcripts, continue processing")
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
    disabled_count = 0
    error_count = 0
    
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
        elif transcript is None:
            # Mark as disabled so we don't retry
            mark_as_disabled(video_id)
            print(f"  ⊘ Transcript disabled/unavailable - marked to skip in future")
            disabled_count += 1
        else:
            print(f"  ❌ Error occurred")
            error_count += 1
        
        # Wait before next video (unless it's the last one)
        if i < len(videos):
            print(f"  ⏳ Waiting 20 seconds...")
            time.sleep(20)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"BATCH COMPLETE")
    print(f"  ✓ Successful: {success_count}")
    print(f"  ⊘ Disabled/Unavailable: {disabled_count}")
    print(f"  ❌ Errors: {error_count}")
    print(f"  Total processed: {len(videos)}")
    
    if success_count > 0:
        print(f"\n🎉 Successfully fetched {success_count} transcripts!")
    if disabled_count > 0:
        print(f"\n💡 {disabled_count} videos don't have transcripts available")
        print(f"   Run again to continue with remaining videos")
    print("=" * 60)

if __name__ == '__main__':
    main()
