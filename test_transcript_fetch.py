#!/usr/bin/env python3
"""
Test transcript fetching for various videos
"""
import sys
sys.path.insert(0, 'scripts')
from fetch_and_store import fetch_transcript_youtube_api

# Test a mix of videos - some from 2025 (working) and some older
test_videos = [
    ('QFcWRmOIEkY', '2025 - Should work'),
    ('M8sc01mZA4U', '2014 - Empty'),
    ('gSuSrGRPTx8', '2014 - Empty'),
    ('BV5gwxjnniI', '2017 - Empty'),
    ('nD9oDfikXQ0', '2015 - Empty'),
]

print("Testing YouTube transcript API:\n")
for video_id, desc in test_videos:
    print(f"Video: {video_id} ({desc})")
    try:
        transcript = fetch_transcript_youtube_api(video_id)
        if transcript:
            print(f"  ✅ SUCCESS - Length: {len(transcript)} chars")
            print(f"  Preview: {transcript[:100]}...")
        else:
            print(f"  ❌ FAILED - No transcript returned")
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
    print()
