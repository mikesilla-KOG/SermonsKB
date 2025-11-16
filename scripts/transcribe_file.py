#!/usr/bin/env python3
"""
Transcribe a local audio file with local Whisper and insert into `sermons.db`.

Usage:
  python3 scripts/transcribe_file.py /path/to/audio.mp3 --video-id <ID> --title "Title" --published-at "YYYY-MM-DD"

This duplicates the DB insert behavior used by `scripts/fetch_and_store.py` so you can
test a single-file end-to-end without relying on `yt-dlp`.
"""
import os
import sys
import json
import sqlite3
import argparse
from datetime import datetime

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    if not text:
        return []
    chunks = []
    start = 0
    L = len(text)
    while start < L:
        end = min(start + size, L)
        chunks.append(text[start:end])
        if end == L:
            break
        start = max(0, end - overlap)
    return chunks


def write_transcript_json(video_id, title, published_at, transcript, out_dir="data/transcripts"):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{video_id}.json")
    payload = {
        "video_id": video_id,
        "title": title,
        "published_at": published_at,
        "transcript": transcript,
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return path


def insert_into_db(db_path, video_id, title, published_at, transcript):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Insert/replace into sermons (FTS5 table should accept inserts)
    cur.execute(
        "INSERT OR REPLACE INTO sermons(video_id, title, published_at, transcript) VALUES (?, ?, ?, ?)",
        (video_id, title, published_at, transcript),
    )
    # Remove old chunks for this video
    cur.execute("DELETE FROM chunks WHERE video_id = ?", (video_id,))
    # Insert chunk rows
    chunks = chunk_text(transcript)
    for chunk in chunks:
        cur.execute("INSERT INTO chunks(video_id, chunk_text) VALUES (?, ?)", (video_id, chunk))
    conn.commit()
    conn.close()
    return len(chunks)


def transcribe_with_whisper(audio_path, model_name=None):
    try:
        import whisper
    except Exception as e:
        print("ERROR: whisper not installed or failed to import:", e)
        return None

    if model_name is None:
        model_name = os.getenv("LOCAL_WHISPER_MODEL", "tiny")
    print(f"Loading Whisper model '{model_name}' (this may take a moment)...")
    try:
        model = whisper.load_model(model_name)
    except Exception as e:
        print("ERROR loading Whisper model:", e)
        return None

    print("Transcribing...")
    try:
        res = model.transcribe(audio_path)
        return res.get("text", "")
    except Exception as e:
        print("ERROR during transcription:", e)
        return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("audio", help="Path to audio file (mp3/wav/m4a/etc)")
    p.add_argument("--video-id", required=True, help="Label to use for video_id in DB and file name")
    p.add_argument("--title", default="", help="Title metadata")
    p.add_argument("--published-at", default=None, help="Published date (ISO) or leave blank)")
    p.add_argument("--db", default="sermons.db", help="Path to sqlite DB")
    args = p.parse_args()

    audio_path = args.audio
    if not os.path.isfile(audio_path):
        print("Audio file not found:", audio_path)
        sys.exit(2)

    published_at = args.published_at or datetime.utcnow().isoformat()

    transcript = transcribe_with_whisper(audio_path)
    if transcript is None:
        print("Transcription failed.")
        sys.exit(1)

    json_path = write_transcript_json(args.video_id, args.title, published_at, transcript)
    n_chunks = insert_into_db(args.db, args.video_id, args.title, published_at, transcript)

    print("Done.")
    print(f"Transcript JSON: {json_path}")
    print(f"Inserted {n_chunks} chunks into DB '{args.db}' for video_id {args.video_id}")


if __name__ == "__main__":
    main()
