# SermonsKB — Project Status & Next Steps

Purpose
- Keep a single, persistent summary of goals, what we've done, known issues, and recommended next steps so you don't need to re-explain the project.

Project goals
- Transcribe all sermons from the YouTube channel `https://www.youtube.com/@vinecluster3113`.
- Store transcripts and chunk them for semantic search.
- Build embeddings and a FAISS index to support a Streamlit QA UI that answers Bible-topic questions using the transcripts (RAG).
- Prefer free/local tooling where possible (local Whisper for transcription, local sentence-transformers for embeddings).

Workspace overview (important files)
- `scripts/fetch_and_store.py` — lists videos, fetches metadata, obtains transcripts (YouTube captions, OpenAI fallback, now local Whisper fallback), inserts into `sermons.db`, and creates `chunks`.
- `scripts/build_embeddings.py` — reads `chunks`, builds embeddings (OpenAI or local `sentence-transformers`), writes FAISS index (`faiss_index.faiss`) and `embeddings_meta.json`.
- `app/streamlit_app.py` — Streamlit UI for Keyword Search (SQLite FTS) and Semantic Search (FAISS + optional RAG via OpenAI).
- `data/transcripts/` — directory where per-video JSON transcript backups are saved by `fetch_and_store.py`.
- `sermons.db` — SQLite DB (FTS5 `sermons` virtual table + `chunks` table).
- `bin/yt-dlp` — thin wrapper added to allow subprocess calls that expect an executable `yt-dlp` (may exist locally under `./bin`).

What we've done so far
- Implemented a local Whisper transcription path in `scripts/fetch_and_store.py` (env var `LOCAL_WHISPER_MODEL`, default `tiny`).
- Created a small `./bin/yt-dlp` wrapper so repo scripts calling `yt-dlp` via subprocess can find an executable in PATH.
- Installed local Whisper and CPU PyTorch in the workspace (so offline transcription is available).
- Ran the channel listing and created rows in `sermons.db` (you currently have rows in `sermons`, but `chunks` is empty).

Known issues / blockers
- Many videos are blocked by YouTube's bot-check and require authentication/cookies for `yt-dlp` to download audio: "Sign in to confirm you're not a bot." This prevents automatic downloads in this environment.
- The `youtube-transcript-api` in this environment showed an API mismatch in previous runs (some methods missing). That can be resolved by installing a compatible version or switching approach.
- `sermons` table currently has metadata rows but `transcript` text is empty for many rows (because we couldn't download the audio or captions for transcription).

Options to proceed (pick one)
1) Provide YouTube cookies (export from your browser) so `yt-dlp` can download videos in this environment. This is the most reliable path to complete transcripts for every video.
2) Provide a sample audio file (MP3/WAV) for a sermon — I will run Whisper locally and insert the transcript and chunks into the DB to validate the full pipeline.
3) Use an Invidious instance as `yt-dlp` extractor to bypass the bot-check (works inconsistently). Example instance `https://yewtu.cafe` or other public instances; try a few.
4) Use the YouTube Data API (requires API key and possibly OAuth) to fetch video streams or captions where available — more setup and quota considerations.

Immediate next steps I can carry out for you (choose any):
- Try N more video IDs with `yt-dlp` (without cookies) to find one that downloads. (Quick)
- Try downloading via Invidious instance by passing `--extractor-args "youtube:invidious=http://yewtu.cafe"` to `yt-dlp` and see if that bypasses the bot-check. (Quick)
- If you paste browser-exported cookies, I'll re-run the fetch for all videos and produce transcripts and chunks.
- If you upload one sermon audio file, I will run Whisper locally and finish the DB insert, then build embeddings and run the Streamlit UI locally.

Helpful commands (copy-paste)
- Add `./bin` to PATH for this repo session:
```bash
export PATH="$PWD/bin:$PATH"
```
- Run fetch for a single YouTube video (uses local Whisper if captions not found):
```bash
export LOCAL_WHISPER_MODEL=tiny
export PATH="$PWD/bin:$PATH"
python3 scripts/fetch_and_store.py "https://www.youtube.com/watch?v=<VIDEO_ID>"
```
- Run fetch for a channel (prefer channel `/videos` URL or a prepared JSON list):
```bash
export PATH="$PWD/bin:$PATH"
python3 scripts/fetch_and_store.py "https://www.youtube.com/@vinecluster3113/videos"
```
- If `yt-dlp` requires cookies, export them from your browser (Chrome/Edge/Firefox) using an extension or built-in feature and pass to `yt-dlp` via `--cookies /path/to/cookies.txt`. Example:
```bash
yt-dlp --cookies /path/to/cookies.txt -f bestaudio -o "/tmp/%(id)s.%(ext)s" "https://www.youtube.com/watch?v=<VIDEO_ID>"
```
- Build embeddings and FAISS index (after chunks exist):
```bash
python3 scripts/build_embeddings.py
```
- Run the Streamlit UI locally:
```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

Notes about Whisper model sizes
- `tiny` — fastest, lowest quality (good as a smoke test).
- `base`, `small`, `medium`, `large` — increasing quality and CPU/RAM/time requirements. Use `LOCAL_WHISPER_MODEL=small` or `base` if accuracy is important and resources allow.

Where transcripts are saved
- The script inserts transcripts into `sermons.db` (`sermons.transcript`) and also writes a JSON backup to `data/transcripts/<video_id>.json` (metadata + transcript). Check that folder for raw output.

How to give me cookies safely
- Export cookies to a file (follow yt-dlp docs) and either:
  - Paste the path here and I can read it in this environment (if you upload it), or
  - Run the `yt-dlp` commands locally on your machine with cookies and upload the resulting audio files for me to process.

Short-term recommendation
- If you want quick confirmation of the pipeline, upload one audio file (or allow me to try 3–5 more IDs). If you want full coverage of the channel, provide cookies so the downloader can fetch all videos without manual interruptions.

Status log (latest run)
- `sermons.db` currently shows 40 rows in `sermons` and 0 rows in `chunks` (we attempted channel listing and inserted metadata but `yt-dlp` repeatedly hit the sign-in bot-check on downloads).
- Local Whisper installed; `fetch_and_store.py` updated to use it when needed.

If you'd like me to proceed now, tell me which option above you prefer (try more IDs, try Invidious, provide cookies, or upload one audio file). I'll follow through and update this file with results.

--
Last updated: 2025-11-16
