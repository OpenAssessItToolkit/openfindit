# -*- coding: utf-8 -*-
import subprocess
import os
import sys
from urllib.parse import urlparse, parse_qs
import scrapy
import re
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.utils.httpobj import urlparse
import time
from ..utils import get_id

class FindVideosSpider(scrapy.Spider):
    name = 'findvideos'

    def __init__(self, *args, **kwargs):
        """ Enable urls argument to for start_urls and parse for allowed_domains """
        urls = kwargs.pop('urls', [])
        if urls:
            input = kwargs.get('urls', '').split(',') or []
            self.start_urls = [urls for d in input]
            self.allowed_domains = [urlparse(urls).netloc for d in input]

        filename = kwargs.pop('filename', [])
        if filename:
            with open(filename) as f:
                self.start_urls = [url.strip() for url in f.readlines()]
                self.allowed_domains = [urlparse(url).netloc for url in f.readlines()]

        self.logger.info(self.start_urls)
        super(FindVideosSpider, self).__init__(*args, **kwargs)


    # Constants
    global VIDEO_URLS
    global DOCUMENT_EXT

    SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
    VIDEO_URLS = open(os.path.join(SCRIPT_PATH, '..', 'config', 'findvideos.txt')).read().splitlines()
    DOCUMENT_EXT = open(os.path.join(SCRIPT_PATH, '..', 'config', 'findfiles.txt')).read().splitlines()
    

    def parse(self, response):
        """ Parse all <a>. yield PDF to csv, if not, crawl it  """

        for iframe_tag in response.xpath('//iframe[@src]'):
            # print(iframe_tag.select('@src').extract())
            src = response.urljoin(iframe_tag.attrib['src']).replace("http://", "https://")
            if src.startswith(tuple(VIDEO_URLS)):
                yield scrapy.Request(
                    src,
                    callback = self._parse_video_contents,
                    meta={'metadata': response.meta, 'video_found_as': 'embed', 'on_page': 'YES', 'video_note': 'Captions required.'},
                    dont_filter=True,)
            

        for a_tag in response.xpath('//a[@href]'):
            # print(a_tag.select('@href').extract())
            href = response.urljoin(a_tag.attrib['href']).replace("http://", "https://")
            if urlparse(href).scheme in ('http', 'https'):
                href_clean = href.split('?')[0]
                if href.startswith(tuple(VIDEO_URLS)):
                    # If YouTube, convert to embed URL so we can parse its data directly
                    if ('youtu' in href) and ('embed' not in href):
                        href = "https://www.youtube.com/embed/" + get_id(href)
                    # If the anchor link shows evidence of being a popup overlay
                    if a_tag.css('.fancybox') or a_tag.css('[data-fancybox]') or a_tag.css('.colorbox') or a_tag.css('[data-lightbox]') or a_tag.css('.lbpModal') or a_tag.css('[data-toggle="modal"]') or a_tag.css('.vp-yt-type') or a_tag.css('.vp-vim-type'):
                        on_page = 'YES'
                        video_note = 'Captions required, likely overlay.'
                    else:
                        on_page = 'UNKNOWN'
                        video_note = 'Captions encouraged on off-site links. Required if overlay.'

                    yield scrapy.Request(
                        href,
                        callback = self._parse_video_contents,
                        meta={'metadata': response.meta, 'video_found_as': 'link', 'on_page': on_page, 'video_note': video_note},
                        dont_filter=True,)
                elif href_clean.endswith(tuple(DOCUMENT_EXT)):
                    print('Skip links to documents')
                else:
                    yield scrapy.Request(href, self.parse)

                    
    def _parse_video_contents(self, response):
        """ Inspect video for data """
        video_title = str(response.xpath('//title//text()').extract_first()) or  "UNKNOWN"
        video_title_clean = re.sub(r'\W+', ' ',  video_title)
        video_cc = "UNKNOWN"
        video_duration = "UNKNOWN"
        video_url = response.url
        from_page_url = response.request.headers.get('Referer') or response.status
        if ('/videoseries' and '/playlist' and 'watch_videos' and 'list') not in video_url: # If not playlist take off the query string
            video_url = video_url.split('?')[0]
        try:
            # TODO: Clean this up to only ping once
            cc = ""
            duration = ""
            if response.flags == ['cached']:
                print('OpenFindIt: Cached response. Checking for captions and duration now...')
            else:
                print('OpenFindIt: Un-cached response. Checking for captions and duration (with ~1.5 minute random delay to avoid 429)...')
                time.sleep(randint(61,121)) # if uncached, wait about 1 to 3 minutes between pings
            cc = subprocess.Popen(['youtube-dl', '--no-playlist', '--retries=1', '--list-subs', '--sleep-interval=121', '--max-sleep-interval=131', video_url], stdout=subprocess.PIPE).communicate()[0].decode("utf-8")
            if ('429' in cc) or ('Unable to extract video data' in cc):
                print("OpenFindIt: WARNING! WARNING! WARNING! WARNING! WARNING! WARNING!")
                raise CloseSpider("OpenFindIt: Returned 429 or Unable to extract... - Likely, Too many requests. You're about to get this IP banned. Closing spider.")
            else:
                time.sleep(2)
                duration = subprocess.Popen(['youtube-dl', '--no-playlist', '--retries=1', '--get-duration', '--sleep-interval=122', '--max-sleep-interval=133', video_url], stdout=subprocess.PIPE).communicate()[0].decode("utf-8").rstrip()
            if "Available subtitles for" in cc:
                video_cc = "YES"
            elif ("has no subtitles" in cc) or ("video doesn't have subtitles" in cc):
                video_cc = "NO"
            if ':' in duration:
                video_duration = duration or "UNKNOWN"

        except Exception as ex:
            print(ex)

        yield dict(
            video_url = video_url,
            video_title = video_title_clean,
            from_page_url = from_page_url,
            captioned = video_cc,
            duration = video_duration,
            location = response.meta['video_found_as'],
            on_page = response.meta['on_page'],
            notes = response.meta['video_note']
        )