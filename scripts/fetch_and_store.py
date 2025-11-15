"""
Fetch YouTube video IDs, metadata and transcripts and store them in SQLite (FTS5).

Usage:
  python scripts/fetch_and_store.py channel_or_playlist_url

Behavior:
 - Lists videos via `yt-dlp` (no API key required).
 - Tries `youtube-transcript-api` for captions.
 - If transcript missing and `OPENAI_API_KEY` is set, downloads audio and uses OpenAI's transcription API as a fallback.
 - Stores metadata and transcript into `sermons.db` (FTS table `sermons`) and creates chunk records for embeddings in `chunks`.

Note: Install dependencies from `requirements.txt`.
"""
import os
import sys
import json
import sqlite3
import tempfile
import subprocess
from tqdm import tqdm
from youtube_transcript_api import YouTubeTranscriptApi
import requests
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv('DB_PATH', 'sermons.db')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def ensure_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS sermons USING fts5(video_id, title, published_at, transcript);")
    c.execute("CREATE TABLE IF NOT EXISTS chunks(chunk_id INTEGER PRIMARY KEY AUTOINCREMENT, video_id TEXT, chunk_text TEXT);")
    conn.commit()
    return conn

def get_video_ids_from_url(url):
    # Use yt-dlp to get flat playlist JSON and extract ids
    try:
        cmd = ["yt-dlp", "--flat-playlist", "-J", url]
        cookies = os.getenv('YTDLP_COOKIES')
        if cookies:
            cmd[1:1] = ["--cookies", cookies]
        out = subprocess.check_output(cmd)
        data = json.loads(out)
        ids = [entry.get('id') for entry in data.get('entries', []) if entry.get('id')]
        return ids
    except Exception as e:
        print("Error listing videos with yt-dlp:", e)
        return []

def fetch_meta(video_id):
    try:
        cmd = ["yt-dlp", "-j", f"https://www.youtube.com/watch?v={video_id}"]
        cookies = os.getenv('YTDLP_COOKIES')
        if cookies:
            cmd[1:1] = ["--cookies", cookies]
        out = subprocess.check_output(cmd)
        return json.loads(out)
    except Exception:
        return {}

def fetch_transcript_youtube_api(video_id):
    try:
        segs = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join(s['text'] for s in segs)
    except Exception:
        return None

def download_audio(video_id, dest_path):
    # Uses yt-dlp to extract audio to dest_path (mp3)
    try:
        cmd = [
            "yt-dlp", "-x", "--audio-format", "mp3", "-o", dest_path, f"https://www.youtube.com/watch?v={video_id}"
        ]
        cookies = os.getenv('YTDLP_COOKIES')
        if cookies:
            cmd[1:1] = ["--cookies", cookies]
        subprocess.check_call(cmd)
        return True
    except Exception as e:
        print("Audio download failed:", e)
        return False

def transcribe_with_openai(audio_file_path):
    if not OPENAI_API_KEY:
        return None
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    try:
        with open(audio_file_path, 'rb') as f:
            files = {"file": f}
            data = {"model": "gpt-4o-transcribe"} if True else {"model": "whisper-1"}
            # Use 'whisper-1' or other model compatible with the account. This may need to be adjusted.
            data = {"model": "whisper-1"}
            resp = requests.post(url, headers=headers, data=data, files=files, timeout=300)
        if resp.status_code == 200:
            j = resp.json()
            return j.get('text')
        else:
            print("OpenAI transcription failed:", resp.status_code, resp.text)
            return None
    except Exception as e:
        print("OpenAI transcription error:", e)
        return None

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    L = len(text)
    while start < L:
        end = min(start + size, L)
        chunks.append(text[start:end])
        start = end - overlap
        if start < 0:
            start = 0
        if start >= L:
            break
    return chunks

def insert_into_db(conn, video_id, title, published_at, transcript):
    c = conn.cursor()
    c.execute("INSERT INTO sermons(video_id, title, published_at, transcript) VALUES (?, ?, ?, ?)",
              (video_id, title, published_at, transcript))
    # create chunks
    if transcript:
        for chunk in chunk_text(transcript):
            c.execute("INSERT INTO chunks(video_id, chunk_text) VALUES (?, ?)", (video_id, chunk))
    conn.commit()

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/fetch_and_store.py CHANNEL_OR_PLAYLIST_URL_or_VIDEO_IDS_FILE")
        sys.exit(1)
    arg = sys.argv[1]
    conn = ensure_db()
    ids = []
    # If the arg is a path to an existing file, read video IDs from it (one per line)
    if os.path.exists(arg) and os.path.isfile(arg):
        with open(arg, 'r') as f:
            ids = [line.strip() for line in f.readlines() if line.strip()]
    else:
        ids = get_video_ids_from_url(arg)
    if not ids:
        print("No videos found. Exiting.")
        return
    print(f"Found {len(ids)} videos. Processing...")
    for vid in tqdm(ids):
        # skip if already present
        c = conn.cursor()
        c.execute("SELECT rowid FROM sermons WHERE video_id = ?", (vid,))
        if c.fetchone():
            continue
        meta = fetch_meta(vid)
        title = meta.get('title', '')
        published = meta.get('upload_date', '')
        transcript = fetch_transcript_youtube_api(vid)
        if transcript:
            insert_into_db(conn, vid, title, published, transcript)
            continue
        # fallback: download audio + OpenAI whisper (if key provided)
        if OPENAI_API_KEY:
            with tempfile.TemporaryDirectory() as tmp:
                out_template = os.path.join(tmp, '%(id)s.%(ext)s')
                ok = download_audio(vid, out_template)
                if ok:
                    # find the created file
                    for f in os.listdir(tmp):
                        if f.endswith('.mp3') or f.endswith('.m4a') or f.endswith('.webm'):
                            audio_path = os.path.join(tmp, f)
                            text = transcribe_with_openai(audio_path)
                            if text:
                                insert_into_db(conn, vid, title, published, text)
                                break
                    else:
                        insert_into_db(conn, vid, title, published, '')
                else:
                    insert_into_db(conn, vid, title, published, '')
        else:
            # record metadata without transcript so you can investigate later
            insert_into_db(conn, vid, title, published, '')

    print("All done. DB:", DB_PATH)

if __name__ == '__main__':
    main()
