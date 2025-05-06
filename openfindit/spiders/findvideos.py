# -*- coding: utf-8 -*-
import subprocess
import os
import sys
import re
from urllib.parse import urlparse, parse_qs, unquote
import scrapy
from scrapy.spiders import CrawlSpider
from time import sleep
from ..utils import get_id, normalize_youtube_url, extract_video_metadata

class FindVideosSpider(scrapy.Spider):
    name = 'findvideos'

    def __init__(self, *args, **kwargs):
        urls = kwargs.pop('urls', '')
        filename = kwargs.pop('filename', '')

        if urls:
            input_urls = urls.split(',')
            self.start_urls = [url.strip() for url in input_urls if url.strip()]
        elif filename:
            with open(filename) as f:
                lines = [line.strip() for line in f if line.strip()]
                self.start_urls = self._extract_urls_from_lines(lines)
        else:
            raise ValueError("You must provide either --urls or --filename")

        self.allowed_domains = [urlparse(url).netloc for url in self.start_urls]
        self.logger.info(f"Start URLs: {self.start_urls}")
        super(FindVideosSpider, self).__init__(*args, **kwargs)

        script_path = os.path.dirname(os.path.realpath(__file__))
        self.VIDEO_URLS = open(os.path.join(script_path, '..', 'config', 'findvideos.txt')).read().splitlines()

        self.seen_video_urls = set()

    def _extract_urls_from_lines(self, lines):
        urls = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith("<"):
                match = re.search(r'<loc>(.*?)</loc>', line)
                if match:
                    urls.append(match.group(1).strip())
            else:
                urls.append(line)
        return urls

    def parse(self, response):
        for iframe_tag in response.xpath('//iframe[@src]'):
            src = response.urljoin(iframe_tag.attrib['src']).replace("http://", "https://")
            if "/oembed?url=" in src or "youtu" in src:
                qs = parse_qs(urlparse(src).query)
                actual_url = unquote(qs.get("url", [""])[0])
                if actual_url.startswith(tuple(self.VIDEO_URLS)):
                    src = actual_url

            src = normalize_youtube_url(src)

            if src.startswith(tuple(self.VIDEO_URLS)):
                yield scrapy.Request(
                    src,
                    callback=self._parse_video_contents,
                    meta={'metadata': response.meta, 'video_found_as': 'embed', 'on_page': 'YES', 'video_note': 'Captions required.'},
                    dont_filter=True,
                )

        for a_tag in response.xpath('//a[@href]'):
            href = response.urljoin(a_tag.attrib['href'])
            if href.startswith('#') or href.startswith('mailto:'):
                continue

            if urlparse(href).scheme in ('http', 'https'):
                if href.startswith(tuple(self.VIDEO_URLS)):
                    href = normalize_youtube_url(href)
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
                elif urlparse(href).netloc in self.allowed_domains:
                    yield scrapy.Request(href, self.parse)
                else:
                    yield scrapy.Request(href, self.parse)

    def _parse_video_contents(self, response):
        video_url = normalize_youtube_url(response.url)
        parsed = urlparse(video_url)
        if "youtube" not in parsed.netloc and "youtu.be" not in parsed.netloc:
            video_url = parsed.scheme + "://" + parsed.netloc + parsed.path

        if video_url in self.seen_video_urls:
            return
        self.seen_video_urls.add(video_url)

        video_title = response.xpath('//title/text()').get(default='').strip()
        if video_title.lower() == 'youtube' or not video_title:
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
            duration, captioned, views = extract_video_metadata(video_url)
        except Exception as ex:
            self.logger.warning(f"Error processing video: {ex}")
            duration = captioned = views = "UNKNOWN"

        yield dict(
            video_url=video_url,
            video_title=video_title_clean,
            from_page_url=response.request.headers.get('Referer', b'').decode('utf-8', 'ignore'),
            captioned=captioned,
            duration=duration,
            view_count=views,
            location=response.meta['video_found_as'],
            on_page=response.meta['on_page'],
            notes=response.meta['video_note']
        )
