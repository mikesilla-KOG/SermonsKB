"""
Simple manual transcript importer
Paste or load transcript text and save to database
Flexible format - can handle title, date, and transcript in any reasonable format
"""
import sqlite3
import sys
import os
import re

def parse_content(content):
    """
    Try to extract title, date, and transcript from pasted content
    Flexible - handles various formats, removes timestamps
    """
    lines = [line.strip() for line in content.strip().split('\n') if line.strip()]
    
    if not lines:
        return None, None, content
    
    title = None
    date = None
    transcript_lines = []
    transcript_start = 0
    
    # Try to find title (usually first line, might have labels like "Title:")
    if lines:
        first_line = lines[0]
        # Remove common prefixes
        title = re.sub(r'^(title|subject|sermon):\s*', '', first_line, flags=re.IGNORECASE).strip()
        transcript_start = 1
    
    # Try to find date in first few lines
    for i, line in enumerate(lines[:3]):
        # Look for date patterns
        date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\w+ \d{1,2},? \d{4}|date:\s*\S+)', line, re.IGNORECASE)
        if date_match:
            date = date_match.group(1).replace('date:', '').strip()
            if i >= transcript_start:
                transcript_start = i + 1
            break
    
    # Process transcript lines - remove timestamps
    for line in lines[transcript_start:]:
        # Remove timestamps like [00:00:00], (00:00), 0:00:00, etc.
        cleaned = re.sub(r'\[?\(?\d{1,2}:\d{2}(?::\d{2})?\)?\]?', '', line)
        # Remove standalone timestamps at start of line
        cleaned = re.sub(r'^\d{1,2}:\d{2}(?::\d{2})?\s+', '', cleaned)
        cleaned = cleaned.strip()
        if cleaned:
            transcript_lines.append(cleaned)
    
    transcript = '\n'.join(transcript_lines).strip()
    
    return title, date, transcript

def import_transcript_from_text(video_id, content_text):
    """Import transcript directly from text (can include title and date)"""
    conn = sqlite3.connect('sermons.db')
    cursor = conn.cursor()
    
    # Parse the content
    title, date, transcript = parse_content(content_text)
    
    if not transcript:
        print(f"❌ No transcript text found")
        conn.close()
        return False
    
    # Check if video exists
    cursor.execute('SELECT video_id, title, published_at FROM sermons WHERE video_id = ?', (video_id,))
    result = cursor.fetchone()
    
    if result:
        # Update existing video
        existing_title = result[1]
        existing_date = result[2]
        
        # Use parsed values or keep existing
        final_title = title if title else existing_title
        final_date = date if date else existing_date
        
        cursor.execute('''
            UPDATE sermons 
            SET transcript = ?, title = ?, published_at = ?
            WHERE video_id = ?
        ''', (transcript, final_title, final_date, video_id))
        
        print(f"✅ Updated existing video:")
    else:
        # Insert new video
        final_title = title if title else "Untitled"
        final_date = date if date else ""
        
        cursor.execute('''
            INSERT INTO sermons (video_id, title, published_at, transcript)
            VALUES (?, ?, ?, ?)
        ''', (video_id, final_title, final_date, transcript))
        
        print(f"✅ Created new video entry:")
    
    conn.commit()
    conn.close()
    
    print(f"   Video ID:   {video_id}")
    print(f"   Title:      {final_title}")
    print(f"   Date:       {final_date}")
    print(f"   Transcript: {len(transcript)} characters")
    return True

def import_transcript_from_file(video_id, file_path):
    """Import transcript from a text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            transcript_text = f.read()
        return import_transcript_from_text(video_id, transcript_text)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False

def generate_video_id(title, date):
    """Generate a video ID from title and date"""
    import hashlib
    from datetime import datetime
    
    # Use title and date to create unique ID
    base = f"{title}-{date}".lower()
    # Remove special characters, keep alphanumeric and spaces
    base = re.sub(r'[^a-z0-9\s-]', '', base)
    # Replace spaces with hyphens
    base = re.sub(r'\s+', '-', base)
    # Remove multiple hyphens
    base = re.sub(r'-+', '-', base)
    # Limit length
    base = base[:50].strip('-')
    
    # Add hash for uniqueness
    hash_part = hashlib.md5(f"{title}{date}".encode()).hexdigest()[:8]
    
    return f"{base}-{hash_part}"

def import_multiple_from_file(file_path):
    """Import multiple transcripts from one file, separated by --- markers"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by 3 or more hyphens (---) which marks sermon boundaries
        # Allow spaces before/after the hyphens
        import re
        sections = re.split(r'\n\s*-{3,}\s*\n', content)
        
        # Filter out empty sections
        sections = [s.strip() for s in sections if s.strip() and len(s) > 100]
        
        print(f"\nFound {len(sections)} sections in file")
        print("=" * 60)
        
        success_count = 0
        for i, section in enumerate(sections, 1):
            print(f"\n--- Section {i}/{len(sections)} ---")
            
            # Parse to get title and date for generating ID
            title, date, transcript = parse_content(section)
            
            if not transcript or len(transcript) < 100:
                print("❌ No transcript found or too short, skipping")
                continue
            
            # Generate video ID
            video_id = generate_video_id(
                title if title else f"sermon-{i}", 
                date if date else "unknown"
            )
            
            print(f"Generated ID: {video_id}")
            
            if import_transcript_from_text(video_id, section):
                success_count += 1
        
        print("\n" + "=" * 60)
        print(f"✅ Successfully imported {success_count}/{len(sections)} transcripts")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        import traceback
        traceback.print_exc()
        return False

def interactive_import():
    """Interactive mode for pasting transcript"""
    print("=" * 60)
    print("Manual Transcript Importer")
    print("=" * 60)
    
    video_id = input("\nEnter video ID: ").strip()
    
    if not video_id:
        print("❌ Video ID required")
        return
    
    print("\nChoose input method:")
    print("1. Paste transcript (end with Ctrl+Z on new line, then Enter)")
    print("2. Load from file")
    
    choice = input("\nChoice (1 or 2): ").strip()
    
    if choice == "1":
        print("\nPaste transcript below (Ctrl+Z + Enter when done):")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        
        transcript_text = '\n'.join(lines)
        import_transcript_from_text(video_id, transcript_text)
        
    elif choice == "2":
        file_path = input("\nEnter file path: ").strip()
        import_transcript_from_file(video_id, file_path)
    else:
        print("❌ Invalid choice")

def main():
    if len(sys.argv) == 1:
        # Interactive mode
        interactive_import()
    elif len(sys.argv) == 2:
        # Multiple transcripts from one file: python import_transcript_manual.py FILE_PATH
        file_path = sys.argv[1]
        import_multiple_from_file(file_path)
    elif len(sys.argv) == 3:
        # Single transcript from file: python import_transcript_manual.py VIDEO_ID FILE_PATH
        video_id = sys.argv[1]
        file_path = sys.argv[2]
        import_transcript_from_file(video_id, file_path)
    else:
        print("Usage:")
        print("  Interactive:        python import_transcript_manual.py")
        print("  Multiple from file: python import_transcript_manual.py FILE_PATH")
        print("  Single from file:   python import_transcript_manual.py VIDEO_ID FILE_PATH")

if __name__ == '__main__':
    main()
