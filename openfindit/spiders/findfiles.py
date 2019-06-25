# -*- coding: utf-8 -*-
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.utils.httpobj import urlparse

class FindFilesSpider(scrapy.Spider):
    name = 'findfiles'

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
        super(FindFilesSpider, self).__init__(*args, **kwargs)


    def parse(self, response):
        """ Parse all <a>. yield PDF to csv, if not, crawl it  """
        for a_tag in response.xpath('//a[@href]'):

            url = response.urljoin(a_tag.attrib['href'])

            if urlparse(url).scheme in ('http', 'https'):

                if url.endswith(('.pdf', '.docx', '.pptx', '.xlsx')):
                    yield {
                        'url' : url,
                        'link_text' : a_tag.xpath('.//text()').get(),
                        'from_page_url' : response.url
                    }

                elif 'http' in urlparse(url).scheme:
                    yield scrapy.Request(url, self.parse)
