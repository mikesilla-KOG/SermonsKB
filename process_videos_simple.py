"""
Simple video processor that handles one video at a time
Designed to avoid subprocess interruption issues
"""
import os
import sys
import time
import sqlite3
from scripts.transcribe_google import download_and_transcribe_google

def get_videos_needing_transcription(db_path='sermons.db'):
    """Get list of video IDs that need transcription"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT video_id FROM sermons WHERE length(transcript) = 0 OR transcript IS NULL')
    video_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return video_ids

def update_transcript(video_id, transcript, db_path='sermons.db'):
    """Update transcript in database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE sermons SET transcript = ? WHERE video_id = ?', (transcript, video_id))
    conn.commit()
    conn.close()

def process_one_video(video_id):
    """Process a single video"""
    print(f"\n{'='*60}")
    print(f"Processing: {video_id}")
    print(f"{'='*60}")
    
    try:
        transcript = download_and_transcribe_google(video_id)
        if transcript:
            update_transcript(video_id, transcript)
            print(f"✅ Success! Transcript length: {len(transcript)} chars")
            return True
        else:
            print(f"❌ Failed to get transcript")
            return False
    except KeyboardInterrupt:
        print(f"\n⚠️  Interrupted by user")
        raise
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    # Set environment variables
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'google-credentials.json'
    os.environ['GOOGLE_CLOUD_BUCKET'] = 'sermons-transcription-temp'
    
    print("Sermon Transcription Processor")
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get videos needing transcription
    videos = get_videos_needing_transcription()
    print(f"\nFound {len(videos)} videos needing transcription")
    
    if not videos:
        print("No videos to process!")
        return
    
    # Process videos one at a time
    success_count = 0
    fail_count = 0
    
    for i, video_id in enumerate(videos, 1):
        print(f"\nProgress: {i}/{len(videos)} ({i/len(videos)*100:.1f}%)")
        
        try:
            if process_one_video(video_id):
                success_count += 1
            else:
                fail_count += 1
        except KeyboardInterrupt:
            print(f"\n\nStopping... Processed {success_count} successfully, {fail_count} failed")
            break
        
        # Brief pause between videos
        if i < len(videos):
            time.sleep(2)
    
    print(f"\n{'='*60}")
    print(f"Processing complete!")
    print(f"Successful: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Remaining: {len(videos) - success_count - fail_count}")
    print(f"Finished at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(1)
