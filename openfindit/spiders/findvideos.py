import subprocess
import os
import re
from urllib.parse import urlparse, parse_qs, unquote
import scrapy
from scrapy_playwright.page import PageMethod
from ..utils import get_id, normalize_youtube_url, extract_video_metadata
import xml.etree.ElementTree as ET


class FindVideosSpider(scrapy.Spider):
    name = 'findvideos'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        urls = kwargs.pop('urls', '')
        filename = kwargs.pop('filename', '')
        sitemap_url = kwargs.pop('sitemap_url', '')

        if urls:
            input_urls = urls.split(',')
            self.input_urls = [url.strip() for url in input_urls if url.strip()]
        elif filename:
            with open(filename) as f:
                lines = [line.strip() for line in f if line.strip()]
                self.input_urls = self._extract_urls_from_lines(lines)
        elif sitemap_url:
            self.input_urls = self._extract_urls_from_sitemap(sitemap_url)
        else:
            raise ValueError("You must provide --urls, --filename, or --sitemap_url")

        self.allowed_domains = [urlparse(url).netloc for url in self.input_urls]

        script_path = os.path.dirname(os.path.realpath(__file__))
        self.VIDEO_URLS = open(os.path.join(script_path, '..', 'config', 'findvideos.txt')).read().splitlines()
        self.DOCUMENT_EXT = open(os.path.join(script_path, '..', 'config', 'findfiles.txt')).read().splitlines()

        self.seen_video_ids = set()

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

    def _extract_urls_from_sitemap(self, sitemap_url):
        try:
            import requests
            response = requests.get(sitemap_url)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            urls = []

            ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            if root.tag.endswith('sitemapindex'):
                for sitemap in root.findall('ns:sitemap', ns):
                    loc = sitemap.find('ns:loc', ns)
                    if loc is not None and loc.text:
                        urls.extend(self._extract_urls_from_sitemap(loc.text.strip()))
            elif root.tag.endswith('urlset'):
                for url in root.findall('ns:url', ns):
                    loc = url.find('ns:loc', ns)
                    if loc is not None and loc.text:
                        urls.append(loc.text.strip())
            return urls
        except Exception as e:
            self.logger.error(f"Failed to parse sitemap: {e}")
            return []

    def _extract_youtube_id(self, url):
        """Primitive YouTube ID extractor from common formats"""
        patterns = [
            r'youtu\.be/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def start_requests(self):
        for url in getattr(self, 'input_urls', []):
            self.logger.info(f"[start_requests] Dispatching request for {url}")
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "domcontentloaded"),
                        PageMethod("wait_for_timeout", 6000),
                        PageMethod("evaluate", """
                            (async () => {
                                const players = Array.from(document.querySelectorAll('div.react-player, div.player-wrapper'));
                                for (const el of players) {
                                    el.scrollIntoView({block: 'center'});
                                    await new Promise(r => setTimeout(r, 500));
                                    el.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
                                    el.dispatchEvent(new MouseEvent('mousemove', { bubbles: true }));
                                    el.click();
                                    await new Promise(r => setTimeout(r, 3000));
                                }
                            })();
                        """),
                        PageMethod("evaluate", "window.dispatchEvent(new Event('scroll'));"),
                        PageMethod("evaluate", "window.dispatchEvent(new Event('resize'));"),
                        PageMethod("wait_for_timeout", 2000),
                        PageMethod("wait_for_selector", "iframe[src*='youtube.com']", timeout=10000),
                    ]
                },
                dont_filter=True
            )

    def parse(self, response):
        for iframe_tag in response.xpath('//iframe[@src]'):
            src = response.urljoin(iframe_tag.attrib['src']).replace("http://", "https://")
            if "/oembed?url=" in src or "youtu" in src:
                qs = parse_qs(urlparse(src).query)
                actual_url = unquote(qs.get("url", [""])[0])
                if actual_url.startswith(tuple(self.VIDEO_URLS)):
                    src = actual_url

            src = normalize_youtube_url(src)
            video_id = self._extract_youtube_id(src)

            if src.startswith(tuple(self.VIDEO_URLS)) and video_id and video_id not in self.seen_video_ids:
                self.seen_video_ids.add(video_id)
                clean_url = f"https://youtube.com/watch?v={video_id}"
                yield scrapy.Request(
                    clean_url,
                    callback=self._parse_video_contents,
                    meta={
                        'metadata': response.meta,
                        'video_found_as': 'embed',
                        'on_page': 'YES',
                        'video_note': 'Captions required.'
                    },
                    dont_filter=True,
                )

        for a_tag in response.xpath('//a[@href]'):
            href = response.urljoin(a_tag.attrib['href'])
            if href.startswith('#') or href.startswith('mailto:'):
                continue

            if urlparse(href).scheme in ('http', 'https'):
                if href.startswith(tuple(self.VIDEO_URLS)):
                    href = normalize_youtube_url(href)
                    video_id = self._extract_youtube_id(href)
                    if video_id and video_id not in self.seen_video_ids:
                        self.seen_video_ids.add(video_id)
                        clean_url = f"https://youtube.com/watch?v={video_id}"

                        on_page = 'YES' if any(a_tag.css(selector) for selector in [
                            '.fancybox', '[data-fancybox]', '.colorbox', '[data-lightbox]', '.lbpModal',
                            '[data-toggle="modal"]', '.vp-yt-type', '.vp-vim-type'
                        ]) else 'UNKNOWN'

                        video_note = 'Captions required, likely overlay.' if on_page == 'YES' else 'Captions encouraged on off-site links. Required if overlay.'

                        yield scrapy.Request(
                            clean_url,
                            callback=self._parse_video_contents,
                            meta={
                                'metadata': response.meta,
                                'video_found_as': 'link',
                                'on_page': on_page,
                                'video_note': video_note
                            },
                            dont_filter=True,
                        )
                elif href.endswith(tuple(self.DOCUMENT_EXT)):
                    continue
                elif urlparse(href).netloc in self.allowed_domains:
                    yield scrapy.Request(href, self.parse, meta={"playwright": True})
                else:
                    yield scrapy.Request(href, self.parse, meta={"playwright": True})

    def _parse_video_contents(self, response):
        video_id = self._extract_youtube_id(response.url)
        video_url = f"https://youtube.com/watch?v={video_id}" if video_id else response.url

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
