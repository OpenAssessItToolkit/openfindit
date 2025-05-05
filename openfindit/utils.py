from scrapy.utils.httpobj import urlparse
from urllib.parse import urlparse, parse_qs

def get_youtube_id_from_oembed(oembed_url):
    qs = parse_qs(urlparse(oembed_url).query)
    encoded_url = qs.get("url", [""])[0]
    actual_url = unquote(encoded_url)
    return get_id(actual_url)

def get_id(url):
    """ parse YouTube urls for id """
    u_pars = urlparse(url)
    quer_v = parse_qs(u_pars.query).get('v')
    if quer_v:
        return quer_v[0]
    pth = u_pars.path.split('/')
    if pth:
        return pth[-1]

def normalize_youtube_url(url):
    """
    Normalize any YouTube URL (embed, shortlink, oembed, etc.) to standard watch?v= format.
    Returns the canonical URL or the original if it can't be parsed.
    """
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    path = parsed.path
    query = parse_qs(parsed.query)

    if 'youtu.be' in netloc:
        # https://youtu.be/VIDEO_ID
        video_id = path.lstrip('/')
    elif 'youtube.com' in netloc:
        if path.startswith('/watch'):
            video_id = query.get('v', [None])[0]
        elif path.startswith('/embed/'):
            video_id = path.split('/embed/')[-1].split('/')[0]
        elif path.startswith('/v/'):
            video_id = path.split('/v/')[-1].split('/')[0]
        elif path.contains('?'):
            video_id = path.split('?')[0]
        else:
            video_id = None
    else:
        return url  # Not a YouTube domain

    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

def cc_status(cc):
    """ parse for captions """
    if "Available subtitles for" in cc:
        yield "YES"
    elif "has no subtitles" in cc:
        yield "NO"
    elif "video doesn't have subtitles" in cc:
        yield "NO"
    else:
        yield "UNKNOWN"  