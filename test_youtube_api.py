#!/usr/bin/env python3
"""
Direct test of youtube-transcript-api
"""
from youtube_transcript_api import YouTubeTranscriptApi

test_videos = [
    'QFcWRmOIEkY',  # 2025 - Known working
    'M8sc01mZA4U',  # 2014 - Empty in DB
    'dsIbw4KPAKE',  # 2025 - Known working
]

for test_video in test_videos:
    print(f"\nTesting video: {test_video}")
    
    try:
        api = YouTubeTranscriptApi()
        segments = api.fetch(test_video)
        
        # Handle both dict and object attributes
        texts = []
        for s in segments:
            if hasattr(s, 'text'):
                texts.append(s.text)
            elif isinstance(s, dict):
                texts.append(s.get('text', ''))
        
        transcript = ' '.join(texts)
        print(f"  ✅ SUCCESS - Length: {len(transcript)} chars")
        print(f"  Preview: {transcript[:150]}...")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print(f"  Error type: {type(e).__name__}")
