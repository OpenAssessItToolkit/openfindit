# -*- coding: utf-8 -*-
import subprocess
import os
import sys
from urllib.parse import urlparse, parse_qs, unquote, urljoin
import scrapy
import re
from scrapy.spiders import CrawlSpider
from time import sleep
from ..utils import get_id, normalize_youtube_url


class FindVideosSpider(scrapy.Spider):
    name = 'findvideos'

    def __init__(self, *args, **kwargs):
        """ Allow start_urls from CLI --urls or --filename """
        urls = kwargs.pop('urls', '')
        filename = kwargs.pop('filename', '')

        if urls:
            input_urls = urls.split(',')
            self.start_urls = [url.strip() for url in input_urls if url.strip()]
            self.allowed_domains = [urlparse(url).netloc for url in self.start_urls]

        elif filename:
            with open(filename) as f:
                lines = [line.strip() for line in f if line.strip()]
                self.start_urls = lines
                self.allowed_domains = [urlparse(url).netloc for url in lines]

        else:
            raise ValueError("You must provide either --urls or --filename")

        self.logger.info(f"Start URLs: {self.start_urls}")
        super(FindVideosSpider, self).__init__(*args, **kwargs)

        script_path = os.path.dirname(os.path.realpath(__file__))
        self.VIDEO_URLS = open(os.path.join(script_path, '..', 'config', 'findvideos.txt')).read().splitlines()
        self.DOCUMENT_EXT = open(os.path.join(script_path, '..', 'config', 'findfiles.txt')).read().splitlines()

    def parse(self, response):
        """ Parse all <a> and <iframe> tags. """
        # Handle iframe tags
        for iframe_tag in response.xpath('//iframe[@src]'):
            src = response.urljoin(iframe_tag.attrib['src']).replace("http://", "https://")

            # Handle oEmbed iframe that wraps YouTube
            if "/oembed?url=" in src or "youtu" in src:
                qs = parse_qs(urlparse(src).query)
                actual_url = unquote(qs.get("url", [""])[0])
                if actual_url.startswith(tuple(self.VIDEO_URLS)):
                    src = actual_url  # Use the actual YouTube link

            src = normalize_youtube_url(src)
            
            if src.startswith(tuple(self.VIDEO_URLS)):
                yield scrapy.Request(
                    src,
                    callback=self._parse_video_contents,
                    meta={'metadata': response.meta, 'video_found_as': 'embed', 'on_page': 'YES', 'video_note': 'Captions required.'},
                    dont_filter=True,
                )

        # Handle <a href>
        for a_tag in response.xpath('//a[@href]'):

            href = response.urljoin(a_tag.attrib['href']) # .replace("http://", "https://")
            # href_clean = href.split('?')[0]

            # ⛔️ Skip anchor and mailto links early
            if href.startswith('#') or href.startswith('mailto:'):
                continue
            
            if urlparse(href).scheme in ('http', 'https'):
                if href.startswith(tuple(self.VIDEO_URLS)):
                    # Normalize YouTube links
                    href = normalize_youtube_url(href)

                    # if 'youtu' in href and 'embed' not in href:
                    #     href = "https://www.youtube.com/watch?v=" + get_id(href)

                    on_page = 'YES' if any(a_tag.css(selector) for selector in [
                        '.fancybox', '[data-fancybox]', '.colorbox', '[data-lightbox]', '.lbpModal', '[data-toggle="modal"]', '.vp-yt-type', '.vp-vim-type'
                    ]) else 'UNKNOWN'

                    video_note = 'Captions required, likely overlay.' if on_page == 'YES' else 'Captions encouraged on off-site links. Required if overlay.'

                    yield scrapy.Request(
                        href,
                        callback=self._parse_video_contents,
                        meta={'metadata': response.meta, 'video_found_as': 'link', 'on_page': on_page, 'video_note': video_note},
                        dont_filter=True,
                    )
                elif href.endswith(tuple(self.DOCUMENT_EXT)):
                    sleep(0.1)
                elif urlparse(href).netloc in self.allowed_domains:
                    yield scrapy.Request(href, self.parse)

    def _parse_video_contents(self, response):
        """ Inspect video for title, captions, duration """
        def format_duration(duration_str):
            parts = duration_str.strip().split(':')
            try:
                if len(parts) == 1:
                    seconds = int(parts[0])
                    return f"{seconds // 60}:{seconds % 60:02d}"
                elif len(parts) == 2:
                    minutes, seconds = map(int, parts)
                    return f"{minutes}:{seconds:02d}"
                elif len(parts) == 3:
                    hours, minutes, seconds = map(int, parts)
                    return f"{hours}:{minutes:02d}:{seconds:02d}"
            except ValueError:
                pass
            return "UNKNOWN"

        def get_duration(url):
            url = normalize_youtube_url(url)

            result = subprocess.run(
                ['yt-dlp', '--no-playlist', '--get-duration', url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            if result.returncode == 0:
                duration_raw = result.stdout.strip()
                return format_duration(duration_raw)
            return "UNKNOWN"

        def check_captions(url):
            result = subprocess.run(
                ['yt-dlp', '--no-playlist', '--list-subs', url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            output = result.stdout
            if "Available subtitles for" in output:
                return "YES", output
            elif ("has no subtitles" in output) or ("video doesn't have subtitles" in output):
                return "NO", output
            return "UNKNOWN", output

        video_url = normalize_youtube_url(response.url)

        # Only strip query string for non-YouTube URLs
        parsed = urlparse(video_url)
        if "youtube" not in parsed.netloc and "youtu.be" not in parsed.netloc:
            video_url = parsed.scheme + "://" + parsed.netloc + parsed.path

        video_title = response.xpath('//title/text()').get(default='').strip()
        if video_title.lower() == 'youtube' or not video_title:
            # Try yt-dlp for a better title
            try:
                result = subprocess.run(
                    ['yt-dlp', '--no-playlist', '--get-title', video_url],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                if result.returncode == 0:
                    video_title = result.stdout.strip()
            except Exception:
                video_title = "UNKNOWN"

        video_title_clean = re.sub(r'\W+', ' ', video_title).strip()

        try:
            video_cc, cc_output = check_captions(video_url)
            if '429' in cc_output or 'Unable to extract video data' in cc_output:
                raise scrapy.exceptions.CloseSpider("Returned 429 or Unable to extract video data")
            video_duration = get_duration(video_url)
            if ':' not in video_duration:
                video_duration = "UNKNOWN"
        except Exception as ex:
            self.logger.warning(f"Error processing video: {ex}")
            video_cc = "UNKNOWN"
            video_duration = "UNKNOWN"

        yield dict(
            video_url=video_url,
            video_title=video_title_clean,
            from_page_url=response.request.headers.get('Referer', b'').decode('utf-8', 'ignore'),
            captioned=video_cc,
            duration=video_duration,
            location=response.meta['video_found_as'],
            on_page=response.meta['on_page'],
            notes=response.meta['video_note']
        )
