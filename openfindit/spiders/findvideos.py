# -*- coding: utf-8 -*-
import subprocess
import os
import sys
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


    def parse(self, response):
        """ Parse all <a>. yield to csv, if not, crawl it  """
        for a_tag in response.xpath('//a[@href]'):

            url = response.urljoin(a_tag.attrib['href'])

            if '.pdf' not in url and urlparse(url).scheme in ('http', 'https'):
                request = scrapy.Request(
                    url, 
                    callback = self.parse_iframe,
                    meta=response.meta, 
                )
                print(response)
                yield request

            elif 'http' in urlparse(url).scheme:

                yield scrapy.Request(url, self.parse)
                

    def parse_iframe(self, response):
        """ Parse all <iframe>. If video yield it to csv """
        for iframe_tag in response.xpath('//iframe[@src]'):
            src = response.urljoin(iframe_tag.attrib['src'])
            print('Found iframe...')
            if src.startswith(('https://youtube', 'https://www.youtube', 'https://youtu.be', 'https://www.youtube-nocookie.com', 'https://player.vimeo', 'https://players.brightcove')):
                print('iframe is a video.')
                request = scrapy.Request(
                    src, 
                    callback = self.parse_iframe_contents, 
                    meta=response.meta, 
                    dont_filter=True,)
                yield request

            else:
                print('iframe not a video.')

    def parse_iframe_contents(self, response):
        video_title = response.xpath('//title//text()').extract_first()
        video_title_clean = re.sub(r'\W+', ' ',  video_title)
        video_url_clean = response.url.split('?')[0]
        video_cc = "UNKNOWN"

        process = subprocess.Popen(['youtube-dl', '--list-subs',  video_url_clean], stdout=subprocess.PIPE)
        caption_status = str(process.communicate()[0])
        print(caption_status)

        if "has no subtitles" in caption_status:
            video_cc = "NO"
        elif "Available subtitles for" in caption_status:
            video_cc = "YES"
        else:
            video_cc = "UNKNOWN"

        yield dict(
            video_url = video_url_clean,
            video_title = video_title_clean,
            from_page_url = response.request.headers.get('Referer'),
            video_cc = video_cc
        )
    
