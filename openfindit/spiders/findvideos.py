# -*- coding: utf-8 -*-
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
        """ Parse all <iframe>. If video yield it to csv """
        for iframe_tag in response.xpath('//iframe[@src]'):
            src = response.urljoin(iframe_tag.attrib['src'])
            
            if src.startswith(('https://youtube', 'https://www.youtube', 'https://youtu.be', 'https://vimeo', 'https://www.vimeo')):

                request = scrapy.Request(
                    src, 
                    callback = self.parse_iframe, 
                    meta=response.meta, 
                    dont_filter=True,)
                yield request

            else:
                # not a video, skip it

    def parse_iframe(self, response):
        video_title = response.xpath('//title//text()').extract_first()
        video_title = re.sub(r'\W+', ' ',  video_title),

        yield dict(
            video_url=response.url,
            video_title = video_title,
            from_page_url = response.request.headers.get('Referer')
        )
    