import shutil
import importlib
import sys

def check_module(name, import_name=None):
    try:
        importlib.import_module(import_name or name)
        print(f"OK: {name}")
        return True
    except Exception as e:
        print(f"MISS: {name} -> {e}")
        return False

def main():
    print("Python:", sys.version)
    ff = shutil.which("ffmpeg")
    print("ffmpeg:", ff or "NOT FOUND in PATH")
    ok = True
    ok &= check_module('yt_dlp')
    ok &= check_module('youtube_transcript_api')
    ok &= check_module('streamlit')
    ok &= check_module('dotenv', 'dotenv')
    ok &= check_module('tqdm')
    ok &= check_module('faiss', 'faiss')
    ok &= check_module('sentence_transformers')
    ok &= check_module('openai')
    ok &= check_module('ffmpeg', 'ffmpeg')
    ok &= check_module('pydub')
    ok &= check_module('whisper')
    print("\nAll good!" if ok else "\nSome items missing. See above to install.")

if __name__ == '__main__':
    main()
