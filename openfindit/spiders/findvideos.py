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
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import get_id


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

    VIDEO_URLS = open(os.getcwd() + '/openfindit/config/findvideos.txt').read().splitlines()

    def parse(self, response):
        """ Parse all <a>. Crawl if same domain  """
        print('MY INFO: parse called')

        for a_tag in response.xpath('//a[@href]'):
            url = response.urljoin(a_tag.attrib['href'])
            if (urlparse(url).scheme in ('http', 'https')):

                yield scrapy.Request(
                    url,
                    callback = self.parse_page_for_video,
                    dont_filter = True,
                    meta={'metadata': response.meta}
                )
            else:
                print('MY INFO: (else) link Not http or https, skip')


    def parse_page_for_video(self, response):
        """ Parse content for potentially embedded videos and forward for inspection. """
        print('MY INFO: called parse_page_for_videos')

        # Search for embedded videos
        for iframe_tag in response.xpath('//iframe[@src]'):
            src = response.urljoin(iframe_tag.attrib['src'])
            print('MY INFO: Found iframe... %s' % src)
            if src.startswith(tuple(VIDEO_URLS)):
                print('MY INFO: (if) iframe has a video %s' % src)
                    
                yield scrapy.Request(
                    src,
                    callback = self.parse_video_contents,
                    meta={'metadata': response.meta, 'video_found_as': 'embed', 'on_page': 'YES', 'video_note': 'Captions required.'},
                    dont_filter=True,)
            else:
                print('MY INFO: (else) iframe not a video.')

        # Search for links to videos
        for a_tag in response.xpath('//a[@href]'):
            href = response.urljoin(a_tag.attrib['href'])

            if href.startswith(tuple(VIDEO_URLS)):
                print('MY INFO: (if) Found link to video %s.' % href)
                # Format YouTube URLs to grab embed url so we can parse it like an iframe
                if ('youtu' in href) and ('embed' not in href):
                    href = "https://www.youtube.com/embed/" + get_id(href)

                yield scrapy.Request(
                    href,
                    callback = self.parse_video_contents,
                    meta={'metadata': response.meta, 'video_found_as': 'link', 'on_page': 'UNKNOWN', 'video_note': 'Captions encouraged on off-site links. Captions required if on-site pop-up.'},
                    dont_filter=False,)
            
            else:
                print('MY INFO: (else) found normal link, send back to self.parse')
                if href.endswith('.pdf'):
                    print('MY INFO: Fuck pdfs. ') # LINKEXTRACTOR is bypassed for some reason.
                else:
                    yield scrapy.Request(
                        href, 
                        self.parse)

        #TODO: Add capability to detect HTML5 <video> tag and parse for <track>.


    def parse_video_contents(self, response):
        video_title = "UNKNOWN"
        video_cc = "UNKNOWN"
        video_duration = "UNKNOWN"
        duration = "UNKNOWN"
        subs = "UNKNOWN"

        video_title = response.xpath('//title//text()').extract_first()
        video_title_clean = re.sub(r'\W+', ' ',  video_title)
        video_url = response.url
        if ('/videoseries' and '/playlist' and 'watch_videos') not in video_url: # Don't crawl playlists
            video_url = video_url.split('?')[0]
            
        # TODO: Clean this up to only ping once
        try:
            print('MY INFO: subprocess placeholder')
            # subs = subprocess.Popen(['youtube-dl', '--list-subs', '--cache-dir=~/tmp', '--sleep-interval 121', '--max-sleep-interval 131', video_url], stdout=subprocess.PIPE).communicate()[0].decode("utf-8")
            # duration = subprocess.Popen(['youtube-dl', '--get-duration', '--cache-dir=~/tmp', '--sleep-interval 122', '--max-sleep-interval 133', video_url], stdout=subprocess.PIPE).communicate()[0].decode("utf-8").rstrip()
        except Exception as ex:
            print(ex)

        if ':' in duration:
            video_duration = duration

        if "Available subtitles for" in subs:
            video_cc = "YES"
        elif "has no subtitles" in subs:
            video_cc = "NO"
        elif "video doesn't have subtitles" in subs:
            video_cc = "NO"
        else:
            video_cc = "UNKNOWN"

        yield dict(
            video_url = video_url,
            video_title = video_title_clean,
            from_page_url = response.request.headers.get('Referer'),
            # captioned = video_cc,
            # duration = video_duration,
            location = response.meta['video_found_as'],
            on_page = response.meta['on_page'],
            # notes = response.meta['video_note']
        )
