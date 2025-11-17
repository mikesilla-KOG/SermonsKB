"""
Quick test to check if YouTube IP ban is lifted
"""
from youtube_transcript_api import YouTubeTranscriptApi
import time

def test_ip_ban():
    test_video = "CHzoSAREEaY"  # A video we know has transcripts
    
    print("Testing if YouTube IP ban is lifted...")
    print(f"Test video: {test_video}")
    print("Attempting to fetch transcript...\n")
    
    try:
        api = YouTubeTranscriptApi()
        transcript_data = api.fetch(test_video)
        text_parts = [s.text for s in transcript_data]
        full_text = ' '.join(text_parts)
        
        print("✅ SUCCESS! IP ban is LIFTED")
        print(f"Fetched {len(full_text)} characters")
        print("\nYou can now resume batch processing with:")
        print("  python fetch_batch_careful.py 50")
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "blocking requests" in error_msg or "RequestBlocked" in str(type(e)):
            print("❌ IP is still BLOCKED")
            print("\nWait a few more hours and try again with:")
            print("  python test_ip_ban.py")
        else:
            print(f"❌ Different error: {e}")
        return False

if __name__ == '__main__':
    test_ip_ban()
