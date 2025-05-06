import subprocess
import json
from urllib.parse import urlparse, parse_qs

def normalize_youtube_url(url):
    """
    Normalize various YouTube URL formats into a standard watch URL.
    """
    parsed = urlparse(url)
    if 'youtu.be' in parsed.netloc:
        video_id = parsed.path.lstrip('/')
        return f'https://www.youtube.com/watch?v={video_id}'
    elif 'youtube.com' in parsed.netloc:
        qs = parse_qs(parsed.query)
        video_id = qs.get('v')
        if video_id:
            return f'https://www.youtube.com/watch?v={video_id[0]}'
    return url

def extract_video_metadata(video_url):
    """
    Use yt-dlp to extract video duration, caption status, and view count.
    """
    try:
        result = subprocess.run(
            ['yt-dlp', '--dump-single-json', '--no-playlist', video_url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            raise Exception(f"yt-dlp failed: {result.stderr}")

        data = json.loads(result.stdout)

        # Format duration into H:MM:SS
        seconds = int(data.get('duration', 0))
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            duration = f"{hours}:{minutes:02}:{seconds:02}"
        else:
            duration = f"{minutes}:{seconds:02}"

        view_count = str(data.get('view_count', 'UNKNOWN'))

        subtitles = data.get('subtitles') or {}
        auto_captions = data.get('automatic_captions') or {}
        captioned = "YES" if subtitles or auto_captions else "NO"

        return duration, captioned, view_count

    except Exception as e:
        print(f"Error in extract_video_metadata: {e}")
        return "UNKNOWN", "UNKNOWN", "UNKNOWN"

def get_id(url):
    """
    Extract the video ID from a normalized YouTube URL.
    """
    parsed = urlparse(url)
    if 'youtube.com' in parsed.netloc:
        qs = parse_qs(parsed.query)
        return qs.get('v', [''])[0]
    elif 'youtu.be' in parsed.netloc:
        return parsed.path.lstrip('/')
    return ''
