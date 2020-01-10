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
        """ Parse all <a>. if iframe has video parse contents, if not crawl it  """
        try:
            for a_tag in response.xpath('//a[@href]'):
                url = response.urljoin(a_tag.attrib['href'])
                if urlparse(url).scheme in ('http', 'https'):
                    request = scrapy.Request(
                        url,
                        callback = self.parse_iframe,
                        meta={'metadata': response.meta}
                    )
                    yield request
                elif 'http' in urlparse(url).scheme:
                    yield scrapy.Request(url, self.parse)

        except Exception as ex:
            print(ex)


    def parse_iframe(self, response):
        """ Parse all <iframe>. If link, crawl it, if video, pass it on for inspection """
 
        # TODO: Eww, nested function. Fix this.
        def get_id(url):
            u_pars = urlparse(url)
            quer_v = parse_qs(u_pars.query).get('v')
            if quer_v:
                return quer_v[0]
            pth = u_pars.path.split('/')
            if pth:
                return pth[-1]                   


        # Search for embedded videos
        for iframe_tag in response.xpath('//iframe[@src]'):
            src = response.urljoin(iframe_tag.attrib['src'])
            print('INFO: Found iframe... %s' % src)
            if src.startswith(tuple(VIDEO_URLS)):
                print('INFO: iframe has a video %s' % src)
                request = scrapy.Request(
                    src,
                    callback = self.parse_video_contents,
                    meta={'metadata': response.meta, 'video_found_as': 'embed', 'on_page': 'YES', 'video_note': 'Requires captions.'},
                    dont_filter=True,)
                    
                yield request
            else:
                print('INFO: iframe not a video.')

        # Search for links to videos
        for a_tag in response.xpath('//a[@href]'):
            href = response.urljoin(a_tag.attrib['href'])

            if href.startswith(tuple(VIDEO_URLS)):
                print('INFO: Found link to video %s.' % href)
                # Format YouTube URLs to grab embed url so we can parse it like an iframe
                if 'youtu' in href and 'embed' not in href:
                    href = "https://youtube.com/embed/" + get_id(href)
                request = scrapy.Request(
                    href,
                    callback = self.parse_video_contents,
                    meta={'metadata': response.meta, 'video_found_as': 'link', 'on_page': 'UNKNOWN', 'video_note': 'If link is popup video mark the on_page column as YES. Then it must be captioned.'},
                    dont_filter=True,)

                yield request

        #TODO: Add capability to detect HTML5 <video> tag and parse for <track>.


    def parse_video_contents(self, response):
        video_title = "UNKNOWN"
        video_cc = "UNKNOWN"
        video_duration = "UNKNOWN"

        video_title = response.xpath('//title//text()').extract_first()
        video_title_clean = re.sub(r'\W+', ' ',  video_title)
        video_url = response.url
        if ('/videoseries' and '/playlist') not in video_url:
            video_url = video_url.split('?')[0]
            
        # TODO: Clean this up to only ping once
        try:
            subs = subprocess.Popen(['youtube-dl', '--list-subs', video_url], stdout=subprocess.PIPE).communicate()[0].decode("utf-8")
            duration = subprocess.Popen(['youtube-dl', '--get-duration', video_url], stdout=subprocess.PIPE).communicate()[0].decode("utf-8").rstrip()
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
            captioned = video_cc,
            duration = video_duration,
            location = response.meta['video_found_as'],
            on_page = response.meta['on_page'],
            notes = response.meta['video_note']
        )
