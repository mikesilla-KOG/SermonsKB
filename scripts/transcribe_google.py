#!/usr/bin/env python3
"""
Transcribe audio using Google Cloud Speech-to-Text API
"""
import os
import subprocess
import tempfile
from pathlib import Path

def transcribe_with_google_speech(audio_file_path):
    """
    Transcribe audio using Google Cloud Speech-to-Text API via GCS
    Requires GOOGLE_APPLICATION_CREDENTIALS and GOOGLE_CLOUD_BUCKET
    """
    try:
        from google.cloud import speech
        from google.cloud import storage
    except ImportError:
        print("Installing google-cloud-speech and google-cloud-storage...")
        subprocess.check_call(["pip", "install", "google-cloud-speech", "google-cloud-storage"])
        from google.cloud import speech
        from google.cloud import storage
    
    file_size_mb = os.path.getsize(audio_file_path) / 1024 / 1024
    print(f"Audio file size: {file_size_mb:.2f} MB")
    
    # Always use GCS for sermon audio (typically > 1 minute)
    bucket_name = os.getenv('GOOGLE_CLOUD_BUCKET')
    
    if not bucket_name:
        print("ERROR: GOOGLE_CLOUD_BUCKET environment variable not set")
        print("Please create a GCS bucket and set GOOGLE_CLOUD_BUCKET in .env")
        return None
    
    try:
        # Upload to GCS
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob_name = f"sermons-temp/{os.path.basename(audio_file_path)}"
        blob = bucket.blob(blob_name)
        
        print(f"Uploading to gs://{bucket_name}/{blob_name}...")
        blob.upload_from_filename(audio_file_path)
        gcs_uri = f"gs://{bucket_name}/{blob_name}"
        print(f"Upload complete: {gcs_uri}")
        
        # Use GCS URI for transcription
        speech_client = speech.SpeechClient()
        audio = speech.RecognitionAudio(uri=gcs_uri)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.MP3,
            sample_rate_hertz=16000,
            language_code="en-US",
            enable_automatic_punctuation=True,
            model="latest_long",
        )
        
        print("Transcribing with Google Speech API (this may take a few minutes)...")
        operation = speech_client.long_running_recognize(config=config, audio=audio)
        response = operation.result(timeout=600)
        
        # Clean up GCS file
        try:
            blob.delete()
            print("Cleaned up temporary GCS file")
        except Exception as e:
            print(f"Warning: Could not delete temp file: {e}")
        
        transcript = " ".join([result.alternatives[0].transcript for result in response.results])
        return transcript.strip()
        
    except Exception as e:
        print(f"Google Speech error: {e}")
        return None


def download_and_transcribe_google(video_id):
    """
    Download audio with yt-dlp and transcribe with Google Speech API
    """
    try:
        import shlex
        
        with tempfile.TemporaryDirectory() as tmpdir:
            out_template = os.path.join(tmpdir, f'{video_id}.%(ext)s')
            
            # Download audio using yt-dlp
            cmd = [
                "yt-dlp", "-x", "--audio-format", "mp3",
                "--audio-quality", "5",  # Smaller file, faster upload
                "-o", out_template,
                f"https://www.youtube.com/watch?v={video_id}"
            ]
            
            # Add cookies if available
            cookies = os.getenv('YTDLP_COOKIES')
            if cookies:
                cmd[1:1] = ["--cookies", cookies]
            
            print(f"Downloading audio for {video_id}...")
            subprocess.run(cmd, check=True)
            
            # Find the downloaded file
            audio_file = None
            for f in os.listdir(tmpdir):
                if f.endswith('.mp3'):
                    audio_file = os.path.join(tmpdir, f)
                    break
            
            if not audio_file:
                print("No audio file found after download")
                return None
            
            print(f"Audio file size: {os.path.getsize(audio_file) / 1024 / 1024:.2f} MB")
            
            # Transcribe with Google Speech API
            transcript = transcribe_with_google_speech(audio_file)
            return transcript
            
    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == '__main__':
    # Test with a known shorter video
    test_video = 'QFcWRmOIEkY'  # 2025 video that's working
    
    # Check for credentials
    creds = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not creds:
        print("ERROR: GOOGLE_APPLICATION_CREDENTIALS not set!")
        print("Please follow instructions in GOOGLE_SPEECH_SETUP.md")
        exit(1)
    
    if not os.path.exists(creds):
        print(f"ERROR: Credentials file not found: {creds}")
        print("Please download the JSON file from Google Cloud Console")
        exit(1)
    
    print(f"Testing Google Speech API with video: {test_video}\n")
    result = download_and_transcribe_google(test_video)
    
    if result:
        print(f"\n✅ SUCCESS! Transcript length: {len(result)} chars")
        print(f"Preview: {result[:200]}...")
    else:
        print("\n❌ FAILED")
