#!/usr/bin/env python3
"""
Batch processing script for fetching and storing YouTube video transcripts.

Usage:
  python scripts/fetch_batch.py --batch-size 50 --start-index 0
  python scripts/fetch_batch.py --batch-size 50 --start-index 50  # Resume from batch 2
  python scripts/fetch_batch.py --ids-file video_ids.txt --batch-size 25

Features:
- Processes videos in configurable batches
- Skips already-processed videos (checks DB)
- Saves progress after each video
- Can resume from any batch
"""
import os
import sys
import json
import sqlite3
import tempfile
import subprocess
import argparse
from tqdm import tqdm
from youtube_transcript_api import YouTubeTranscriptApi
import requests
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv('DB_PATH', 'sermons.db')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
LOCAL_WHISPER_MODEL = os.getenv('LOCAL_WHISPER_MODEL', 'base')  # Re-enabled for reprocessing
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')  # Google Speech API

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS sermons USING fts5(video_id, title, published_at, transcript);")
    c.execute("CREATE TABLE IF NOT EXISTS chunks(chunk_id INTEGER PRIMARY KEY AUTOINCREMENT, video_id TEXT, chunk_text TEXT);")
    conn.commit()
    return conn


def video_exists(conn, video_id):
    c = conn.cursor()
    c.execute("SELECT rowid FROM sermons WHERE video_id = ?", (video_id,))
    return c.fetchone() is not None


def fetch_meta(video_id):
    try:
        cmd = ["yt-dlp", "-j", f"https://www.youtube.com/watch?v={video_id}"]
        cookies = os.getenv('YTDLP_COOKIES')
        if cookies:
            cmd[1:1] = ["--cookies", cookies]
        extra = os.getenv('YTDLP_EXTRACTOR_ARGS')
        if extra:
            import shlex
            try:
                cmd += shlex.split(extra)
            except Exception:
                cmd.append(extra)
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
        return json.loads(out)
    except Exception:
        return {}


def fetch_transcript_youtube_api(video_id):
    try:
        api = YouTubeTranscriptApi()
        segs = api.fetch(video_id)
        out_parts = []
        for s in segs:
            if hasattr(s, 'text'):
                out_parts.append(s.text)
            elif isinstance(s, dict):
                out_parts.append(s.get('text', ''))
        return " ".join(out_parts)
    except Exception:
        return None


def download_audio(video_id, dest_path):
    try:
        cmd = [
            "yt-dlp", "-x", "--audio-format", "mp3", "-o", dest_path, f"https://www.youtube.com/watch?v={video_id}"
        ]
        cookies = os.getenv('YTDLP_COOKIES')
        if cookies:
            cmd[1:1] = ["--cookies", cookies]
        extra = os.getenv('YTDLP_EXTRACTOR_ARGS')
        if extra:
            import shlex
            try:
                cmd += shlex.split(extra)
            except Exception:
                cmd.append(extra)
        subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"Audio download failed for {video_id}: {e}")
        return False


def transcribe_with_openai(audio_file_path):
    if not OPENAI_API_KEY:
        return None
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    try:
        with open(audio_file_path, 'rb') as f:
            files = {"file": f}
            data = {"model": "whisper-1"}
            resp = requests.post(url, headers=headers, data=data, files=files, timeout=300)
        if resp.status_code == 200:
            j = resp.json()
            return j.get('text')
        else:
            print(f"OpenAI transcription failed: {resp.status_code}")
            return None
    except Exception as e:
        print(f"OpenAI transcription error: {e}")
        return None


def transcribe_with_google_speech(audio_file_path):
    """Transcribe audio using Google Cloud Speech-to-Text API"""
    if not GOOGLE_APPLICATION_CREDENTIALS:
        return None
    
    try:
        from google.cloud import speech
    except ImportError:
        print("google-cloud-speech not installed, skipping...")
        return None
    
    try:
        client = speech.SpeechClient()
        
        with open(audio_file_path, 'rb') as f:
            content = f.read()
        
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_automatic_punctuation=True,
            model="latest_long",
        )
        
        print("Transcribing with Google Speech API...")
        operation = client.long_running_recognize(config=config, audio=audio)
        response = operation.result(timeout=600)
        
        transcript = " ".join([result.alternatives[0].transcript for result in response.results])
        return transcript.strip()
    except Exception as e:
        print(f"Google Speech error: {e}")
        return None


def transcribe_with_whisper(audio_file_path, model_name=LOCAL_WHISPER_MODEL):
    # Check if Whisper is disabled
    if not model_name or model_name.strip() == '':
        print("Whisper transcription disabled (LOCAL_WHISPER_MODEL not set)")
        return None
    
    try:
        import whisper
    except Exception as e:
        print(f"Local Whisper not available: {e}")
        return None
    try:
        print(f"Loading Whisper model '{model_name}'...")
        model = whisper.load_model(model_name)
        print("Transcribing with Whisper...")
        res = model.transcribe(audio_file_path)
        return res.get('text')
    except Exception as e:
        print(f"Whisper transcription error: {e}")
        return None


def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    if not text:
        return []
    chunks = []
    start = 0
    L = len(text)
    max_iterations = (L // (size - overlap)) + 2  # Safety limit
    iteration = 0
    while start < L and iteration < max_iterations:
        end = min(start + size, L)
        chunks.append(text[start:end])
        if end >= L:
            break
        start = end - overlap
        if overlap >= size:  # Prevent infinite loop
            start = end
        iteration += 1
    return chunks


def insert_into_db(conn, video_id, title, published_at, transcript):
    c = conn.cursor()
    # Use INSERT OR REPLACE to handle reprocessing
    c.execute("INSERT OR REPLACE INTO sermons(video_id, title, published_at, transcript) VALUES (?, ?, ?, ?)",
              (video_id, title, published_at, transcript))
    
    # Delete old chunks and insert new ones
    c.execute("DELETE FROM chunks WHERE video_id = ?", (video_id,))
    if transcript:
        for chunk in chunk_text(transcript):
            c.execute("INSERT INTO chunks(video_id, chunk_text) VALUES (?, ?)", (video_id, chunk))
    conn.commit()
    
    # Save transcript JSON
    try:
        os.makedirs('data/transcripts', exist_ok=True)
        out = {
            'video_id': video_id,
            'title': title,
            'published_at': published_at,
            'transcript': transcript
        }
        with open(os.path.join('data', 'transcripts', f"{video_id}.json"), 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False)
    except Exception as e:
        print(f'Failed to save transcript file: {e}')


def process_video(conn, video_id, force_reprocess=False):
    """Process a single video and return success status"""
    if video_exists(conn, video_id) and not force_reprocess:
        return True  # Already processed
    
    meta = fetch_meta(video_id)
    title = meta.get('title', '')
    published = meta.get('upload_date', '')
    
    # Try YouTube API first
    transcript = fetch_transcript_youtube_api(video_id)
    if transcript:
        insert_into_db(conn, video_id, title, published, transcript)
        return True
    
    # Fallback: download audio + transcribe
    if GOOGLE_APPLICATION_CREDENTIALS or LOCAL_WHISPER_MODEL or OPENAI_API_KEY:
        with tempfile.TemporaryDirectory() as tmp:
            out_template = os.path.join(tmp, '%(id)s.%(ext)s')
            if download_audio(video_id, out_template):
                for f in os.listdir(tmp):
                    if f.endswith(('.mp3', '.m4a', '.webm')):
                        audio_path = os.path.join(tmp, f)
                        
                        # Try Google Speech first (fastest, most accurate)
                        if GOOGLE_APPLICATION_CREDENTIALS:
                            text = transcribe_with_google_speech(audio_path)
                            if text:
                                insert_into_db(conn, video_id, title, published, text)
                                return True
                        
                        # Try local Whisper second
                        if LOCAL_WHISPER_MODEL:
                            text = transcribe_with_whisper(audio_path)
                            if text:
                                insert_into_db(conn, video_id, title, published, text)
                                return True
                        
                        # Try OpenAI as final fallback
                        if OPENAI_API_KEY:
                            text = transcribe_with_openai(audio_path)
                            if text:
                                insert_into_db(conn, video_id, title, published, text)
                                return True
    
    # Record metadata without transcript
    insert_into_db(conn, video_id, title, published, '')
    return False


def main():
    parser = argparse.ArgumentParser(description='Process YouTube videos in batches')
    parser.add_argument('--ids-file', default='video_ids.txt', help='File containing video IDs')
    parser.add_argument('--batch-size', type=int, default=50, help='Number of videos per batch')
    parser.add_argument('--start-index', type=int, default=0, help='Start from this video index (0-based)')
    parser.add_argument('--max-videos', type=int, help='Maximum number of videos to process')
    parser.add_argument('--reprocess', action='store_true', help='Reprocess videos even if they exist in DB')
    args = parser.parse_args()
    
    # Load video IDs
    with open(args.ids_file, 'r') as f:
        all_ids = [line.strip() for line in f if line.strip()]
    
    # Calculate batch range
    start_idx = args.start_index
    end_idx = len(all_ids)
    if args.max_videos:
        end_idx = min(start_idx + args.max_videos, len(all_ids))
    
    batch_ids = all_ids[start_idx:end_idx]
    
    print(f"Total videos in file: {len(all_ids)}")
    print(f"Processing videos {start_idx} to {end_idx-1} (batch size: {args.batch_size})")
    print(f"Videos in this run: {len(batch_ids)}")
    
    conn = ensure_db()
    
    # Process with progress bar
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for video_id in tqdm(batch_ids, desc="Processing videos"):
        if video_exists(conn, video_id) and not args.reprocess:
            skip_count += 1
            continue
        
        try:
            success = process_video(conn, video_id, force_reprocess=args.reprocess)
            if success:
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"\nError processing {video_id}: {e}")
            fail_count += 1
    
    print(f"\n=== Batch Complete ===")
    print(f"Successfully processed: {success_count}")
    print(f"Skipped (already in DB): {skip_count}")
    print(f"Failed: {fail_count}")
    print(f"Database: {DB_PATH}")
    
    # Show DB stats
    c = conn.cursor()
    total_sermons = c.execute("SELECT count(*) FROM sermons").fetchone()[0]
    total_chunks = c.execute("SELECT count(*) FROM chunks").fetchone()[0]
    print(f"Total sermons in DB: {total_sermons}")
    print(f"Total chunks in DB: {total_chunks}")


if __name__ == '__main__':
    main()
