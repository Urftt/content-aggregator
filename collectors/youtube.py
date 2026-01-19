"""
YouTube Video Collector

Fetches recent videos from configured YouTube channels and stores them in PostgreSQL.
Filters out YouTube Shorts (videos < 60 seconds).
"""

import os
import re
from datetime import datetime
from typing import Dict, List, Optional

import psycopg2
import yaml
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()


def load_channels() -> List[Dict[str, str]]:
    """Load channel configuration from channels.yaml."""
    with open('channels.yaml', 'r') as f:
        config = yaml.safe_load(f)
    return config['channels']


def get_db_connection():
    """Create PostgreSQL database connection."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


def parse_duration(duration: str) -> Optional[int]:
    """
    Parse ISO 8601 duration (e.g., PT15M33S) to seconds.
    Returns None if parsing fails.
    """
    if not duration:
        return None

    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
    if not match:
        return None

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return hours * 3600 + minutes * 60 + seconds


def get_channel_uploads_playlist_id(channel_id: str) -> str:
    """Convert channel ID to uploads playlist ID."""
    return 'UU' + channel_id[2:]


def fetch_channel_videos(youtube, channel_id: str, channel_name: str, max_results: int = 20) -> List[Dict]:
    """
    Fetch recent videos from a YouTube channel.

    Args:
        youtube: YouTube API client
        channel_id: YouTube channel ID
        channel_name: Human-readable channel name
        max_results: Maximum number of videos to fetch

    Returns:
        List of video dictionaries with metadata
    """
    uploads_playlist_id = get_channel_uploads_playlist_id(channel_id)
    videos = []

    # Fetch playlist items (recent uploads)
    playlist_request = youtube.playlistItems().list(
        part='contentDetails',
        playlistId=uploads_playlist_id,
        maxResults=max_results
    )
    playlist_response = playlist_request.execute()

    video_ids = [item['contentDetails']['videoId'] for item in playlist_response.get('items', [])]

    if not video_ids:
        return videos

    # Fetch video details (duration, title, description, etc.)
    videos_request = youtube.videos().list(
        part='snippet,contentDetails',
        id=','.join(video_ids)
    )
    videos_response = videos_request.execute()

    for video in videos_response.get('items', []):
        snippet = video['snippet']
        content_details = video['contentDetails']

        duration_seconds = parse_duration(content_details['duration'])

        # Filter out shorts (< 60 seconds)
        if duration_seconds and duration_seconds < 60:
            continue

        video_data = {
            'video_id': video['id'],
            'title': snippet['title'],
            'url': f"https://www.youtube.com/watch?v={video['id']}",
            'description': snippet.get('description', ''),
            'thumbnail': snippet['thumbnails'].get('high', {}).get('url', ''),
            'published_at': snippet['publishedAt'],
            'channel_name': channel_name,
            'duration_seconds': duration_seconds
        }
        videos.append(video_data)

    return videos


def insert_video(conn, video: Dict) -> bool:
    """
    Insert video into database. Returns True if inserted, False if duplicate.
    """
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO content (
                title, url, source_type, source_name, description,
                thumbnail, published_at, estimated_duration
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            video['title'],
            video['url'],
            'youtube',
            video['channel_name'],
            video['description'],
            video['thumbnail'],
            video['published_at'],
            video['duration_seconds']
        ))
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        # Video already exists (unique URL constraint)
        conn.rollback()
        return False
    finally:
        cursor.close()


def main():
    """Main collector function."""
    print("🚀 Starting YouTube collector...\n")

    # Initialize YouTube API
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        print("❌ Error: YOUTUBE_API_KEY not found in environment variables")
        print("Please copy .env.example to .env and add your API key")
        return

    youtube = build('youtube', 'v3', developerKey=api_key)

    # Load channels
    try:
        channels = load_channels()
    except FileNotFoundError:
        print("❌ Error: channels.yaml not found")
        return

    print(f"📺 Loaded {len(channels)} channels\n")

    # Connect to database
    try:
        conn = get_db_connection()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Make sure PostgreSQL is running: docker-compose up -d postgres")
        return

    # Process each channel
    total_new = 0
    total_skipped = 0

    for channel in channels:
        channel_id = channel['id']
        channel_name = channel['name']

        print(f"📡 Processing: {channel_name}")

        try:
            videos = fetch_channel_videos(youtube, channel_id, channel_name)

            new_count = 0
            for video in videos:
                if insert_video(conn, video):
                    new_count += 1

            skipped_count = len(videos) - new_count
            total_new += new_count
            total_skipped += skipped_count

            print(f"   ✅ Added {new_count} new videos, skipped {skipped_count} duplicates")

        except Exception as e:
            print(f"   ❌ Error processing {channel_name}: {e}")

    conn.close()

    print(f"\n✨ Collection complete!")
    print(f"   📊 Total new videos: {total_new}")
    print(f"   🔄 Total duplicates: {total_skipped}")


if __name__ == '__main__':
    main()
