"""Check if channel_dump.json has caption/subtitle information"""
import json

# Load the channel dump
with open('channel_dump.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Navigate to videos
videos_entry = data['entries'][0]
video_list = videos_entry.get('entries', [])

print(f"Total videos in dump: {len(video_list)}\n")

# Check first few videos for caption info
print("Checking first 5 videos for caption information:")
print("=" * 80)

for i, video in enumerate(video_list[:5], 1):
    video_id = video.get('id', 'N/A')
    title = video.get('title', 'N/A')[:50]
    has_subtitles = 'subtitles' in video
    has_auto_captions = 'automatic_captions' in video
    
    print(f"\n{i}. {video_id} - {title}")
    print(f"   Has 'subtitles' key: {has_subtitles}")
    print(f"   Has 'automatic_captions' key: {has_auto_captions}")
    
    # Check if any caption data exists
    if has_subtitles:
        subtitles = video.get('subtitles', {})
        print(f"   Subtitles languages: {list(subtitles.keys())}")
    
    if has_auto_captions:
        auto_caps = video.get('automatic_captions', {})
        print(f"   Auto-caption languages: {list(auto_caps.keys())}")

print("\n" + "=" * 80)
print("\n💡 Unfortunately, yt-dlp channel dumps don't include caption availability")
print("   info without actually downloading the videos. We'll need to check")
print("   each video individually.")
