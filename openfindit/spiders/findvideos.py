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
import pdb


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
        """ Parse all <a>. yield PDF to csv, if not, crawl it  """
        try:
            for a_tag in response.xpath('//a[@href]'):

                url = response.urljoin(a_tag.attrib['href'])

                if urlparse(url).scheme in ('http', 'https'):
                    request = scrapy.Request(
                        url,
                        callback = self.parse_iframe,
                        meta=response.meta,
                    )
                    yield request

                elif 'http' in urlparse(url).scheme:

                    yield scrapy.Request(url, self.parse)

        except Exception as ex:
            print(ex)


    def parse_iframe(self, response):
        """ Parse all <iframe>. If video yield it to csv """

        videoUrls = [
            'https://youtube.com/watch',
            'https://www.youtube.com/watch',
            'https://youtube.com/v',
            'https://www.youtube.com/v',
            'https://youtu.be/',
            'https://youtube.com/embed',
            'https://www.youtube.com/embed',
            'https://www.youtube-nocookie.com/watch',
            'https://youtube-nocookie.com/watch',
            'https://www.youtube-nocookie.com/v',
            'https://youtube-nocookie.com/v',
            'https://player.vimeo',
            'https://players.brightcove',
            'https://warpwire.duke.edu/w',
            'http://youtube.com/watch',
            'http://www.youtube.com/watch',
            'http://youtube.com/v',
            'http://www.youtube.com/v',
            'http://youtu.be/',
            'http://youtube.com/embed',
            'http://www.youtube.com/embed',
            'http://www.youtube-nocookie.com/watch',
            'http://youtube-nocookie.com/watch',
            'http://www.youtube-nocookie.com/v',
            'http://youtube-nocookie.com/v',
            'http://player.vimeo',
            'http://players.brightcove',
            'http://warpwire.duke.edu/w']


        # TODO: Eww, nested function. Fix this.
        def get_id(url):
            u_pars = urlparse(url)
            quer_v = parse_qs(u_pars.query).get('v')
            if quer_v:
                return quer_v[0]
            pth = u_pars.path.split('/')
            if pth:
                return pth[-1]

        for a_tag in response.xpath('//a[@href]'):
            href = response.urljoin(a_tag.attrib['href'])

            if href.startswith(tuple(videoUrls)):
                print('INFO: Found link to video %s.' % href)
                # Format YouTube URLs to grab embed url so we can parse it like an iframe
                if 'youtu' in href:
                    href = "https://youtube.com/embed/" + get_id(href)

                request = scrapy.Request(
                    href,
                    callback = self.parse_video_contents,
                    meta=response.meta,
                    dont_filter=True,)
                yield request

        for iframe_tag in response.xpath('//iframe[@src]'):
            src = response.urljoin(iframe_tag.attrib['src'])
            print('INFO: Found iframe... %s' % src)
            if src.startswith(tuple(videoUrls)):
                print('INFO: iframe has a video %s' % src)
                request = scrapy.Request(
                    src,
                    callback = self.parse_video_contents,
                    meta=response.meta,
                    dont_filter=True,)
                yield request

            else:
                print('INFO: iframe not a video.')


    def parse_video_contents(self, response):
        video_title = "UNKNOWN"
        video_cc = "UNKNOWN"
        video_duration = "UNKNOWN"

        video_title = response.xpath('//title//text()').extract_first()
        video_title_clean = re.sub(r'\W+', ' ',  video_title)
        video_url_clean = response.url.split('?')[0]

        # TODO: Clean this up to only ping once
        try:
            subs = subprocess.Popen(['youtube-dl', '--list-subs', video_url_clean], stdout=subprocess.PIPE).communicate()[0].decode("utf-8")
            duration = subprocess.Popen(['youtube-dl', '--get-duration', video_url_clean], stdout=subprocess.PIPE).communicate()[0].decode("utf-8").rstrip()

        except Exception as ex:
            print(ex)

        if ':' in duration:
            video_duration = duration

        # subs_status = { "Unsupported URL": "UNKNOWN",
        #                 "Available subtitles for": "YES",
        #                 "has no subtitles": "NO",
        #                 "video doesn't have subtitles": "NO" }

        # video_cc = subs_status.get(subs, "UNKNOWN")
        # print("subs start")
        # print(subs)
        # print("subs end")

        if "Available subtitles for" in subs:
            video_cc = "YES"
        elif "has no subtitles" in subs:
            video_cc = "NO"
        elif "video doesn't have subtitles" in subs:
            video_cc = "NO"
        else:
            video_cc = "UNKNOWN"

        yield dict(
            video_url = video_url_clean,
            video_title = video_title_clean,
            from_page_url = response.request.headers.get('Referer'),
            captioned = video_cc,
            duration = video_duration
        )
