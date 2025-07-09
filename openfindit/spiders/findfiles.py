# -*- coding: utf-8 -*-
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.utils.httpobj import urlparse
import re
import xml.etree.ElementTree as ET
from scrapy_playwright.page import PageMethod

class FindFilesSpider(scrapy.Spider):
    name = 'findfiles'

    def __init__(self, *args, **kwargs):
        """ Enable urls argument to for start_urls and parse for allowed_domains """
        urls = kwargs.pop('urls', '')
        filename = kwargs.pop('filename', '')
        sitemap_url = kwargs.pop('sitemap_url', '')

        if urls:
            input_urls = urls.split(',')
            self.start_urls = [url.strip() for url in input_urls if url.strip()]
        elif filename:
            with open(filename) as f:
                lines = [line.strip() for line in f if line.strip()]
                self.start_urls = self._extract_urls_from_lines(lines)
        elif sitemap_url:
            self.start_urls = self._extract_urls_from_sitemap(sitemap_url)
        else:
            raise ValueError("You must provide --urls, --filename, or --sitemap_url")

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

    def start_requests(self):
        for url in self.start_urls:
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
                    ]
                }
            )

    def parse(self, response):
        """ Parse all <a> links and find documents such as PDFs, DOCs, etc. """
        for a_tag in response.xpath('//a[@href]'):
            url = response.urljoin(a_tag.attrib['href'])

            if urlparse(url).scheme in ('http', 'https'):

                # Check if URL ends with file extensions for documents
                if url.endswith(('.pdf', '.docx', '.pptx', '.xlsx')):
                    yield {
                        'url': url,
                        'link_text': a_tag.xpath('.//text()').get(),
                        'from_page_url': response.url
                    }

                # If the URL is a regular HTTP(s) link, continue crawling
                elif 'http' in urlparse(url).scheme:
                    yield scrapy.Request(url, self.parse, meta={"playwright": True})

    def closed(self, reason):
        print('Scraping complete.,.,.')
