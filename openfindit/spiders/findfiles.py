# -*- coding: utf-8 -*-
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.utils.httpobj import urlparse
from collections.abc import Mapping
import re

class FindFilesSpider(scrapy.Spider):
    name = 'findfiles'
    
    def __init__(self, *args, **kwargs):
        """ Enable urls argument to for start_urls and parse for allowed_domains """
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

        self.logger.info(self.start_urls)
        super(FindFilesSpider, self).__init__(*args, **kwargs)


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
        """ Parse all <a>. yield PDF to csv, if not, crawl it  """
        for a_tag in response.xpath('//a[@href]'):

            url = response.urljoin(a_tag.attrib['href'])
#             print(url)

            if urlparse(url).scheme in ('http', 'https'):

                if url.endswith(('.pdf', '.docx', '.pptx', '.xlsx')):
                    yield {
                        'url' : url,
                        'link_text' : a_tag.xpath('.//text()').get(),
                        'from_page_url' : response.url
                    }

                elif 'http' in urlparse(url).scheme:
                    yield scrapy.Request(url, self.parse)
        
    def closed(self, reason):
        print('Scraping complete.,.,.')

