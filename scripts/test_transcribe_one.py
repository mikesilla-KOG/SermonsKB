import os
import sys
import subprocess
import json
from youtube_transcript_api import YouTubeTranscriptApi
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def try_transcript(video_id):
    print('Testing video:', video_id)
    try:
        t = YouTubeTranscriptApi.get_transcript(video_id)
        text = ' '.join(s['text'] for s in t)
        print('Found transcript length:', len(text))
        return True
    except Exception as e:
        print('No transcript via youtube_transcript_api:', e)
        return False

def download_audio(video_id, dest_dir):
    out_template = os.path.join(dest_dir, f"{video_id}.%(ext)s")
    cmd = ['yt-dlp', '-x', '--audio-format', 'mp3', '-o', out_template, f'https://www.youtube.com/watch?v={video_id}']
    cookies = os.getenv('YTDLP_COOKIES')
    if cookies:
        cmd[1:1] = ['--cookies', cookies]
    print('Running:', ' '.join(cmd))
    try:
        subprocess.check_call(cmd)
        files = [f for f in os.listdir(dest_dir) if f.startswith(video_id)]
        print('Downloaded files:', files)
        return [os.path.join(dest_dir, f) for f in files]
    except subprocess.CalledProcessError as e:
        print('yt-dlp failed:', e)
        return []

def transcribe_openai(audio_path):
    if not OPENAI_API_KEY:
        print('No OPENAI_API_KEY in environment; skipping OpenAI transcription')
        return None
    import requests
    url = 'https://api.openai.com/v1/audio/transcriptions'
    headers = {'Authorization': f'Bearer {OPENAI_API_KEY}'}
    print('Posting audio to OpenAI transcription endpoint (this will use your account).')
    try:
        with open(audio_path, 'rb') as f:
            files = {'file': f}
            data = {'model': 'whisper-1'}
            r = requests.post(url, headers=headers, data=data, files=files, timeout=600)
        print('OpenAI status:', r.status_code)
        try:
            print('OpenAI response:', r.json())
        except Exception:
            print('OpenAI response text:', r.text[:1000])
        if r.status_code == 200:
            return r.json().get('text')
        return None
    except Exception as e:
        print('OpenAI transcription error:', e)
        return None

def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/test_transcribe_one.py VIDEO_ID')
        sys.exit(1)
    vid = sys.argv[1]
    ok = try_transcript(vid)
    if ok:
        return
    tmp = '/tmp/sermon_test'
    os.makedirs(tmp, exist_ok=True)
    files = download_audio(vid, tmp)
    if not files:
        print('No audio downloaded; cannot transcribe.')
        return
    for f in files:
        print('Attempting transcription for', f)
        text = transcribe_openai(f)
        if text:
            print('Transcription length:', len(text))
            # optionally save
            with open(os.path.join(tmp, vid + '.txt'), 'w') as out:
                out.write(text)
            return
    print('No transcription produced for any downloaded file.')

if __name__ == '__main__':
    main()
