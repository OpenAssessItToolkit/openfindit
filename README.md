# OpenFindIt (Work in Progress)

The FindFiles Spider is a little [Scrapy](https://github.com/scrapy/scrapy) script to find documents or videos on a website and send them to a CSV. Use case could be monitoring when new PDF files are uploaded to your website to check for accessibility compliance.

The FindVideos Spider searches for YouTube embeds and sends them to a CSV also. It uses the [youtube-dl](https://github.com/ytdl-org/youtube-dl) library which support parsing metadata in dozens of video formats. Use case could be monitoring when new YouTube videos are embedded on your website so you can manually check if accurate captions exist.

Scrapy is infinitely configurable. This specific crawler implementation features:

- Filters out documents hosted on other domains.
- Uses a slow crawling speed to avoid putting a big load on the server.

You can use it as-is or use it as a template to create your own.

Make sure you have permission to scan the website!

## Overview:

OpenFindIt can be used with [OpenDiffIt](https://github.com/OpenAssessItToolkit/opendiffit) to monitor documents like PDF files that are uploaded to your website. The following is an idea on how they can be used together.

https://youtu.be/OSf31NBB2aE

## OpenFindIt demo:

This is an overview of OpenFindIt functionality.

https://youtu.be/6V9DNIOMyKc

# Using OpenFindIt:

__Prerequisites:__

1. [Start up a virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)

2. Install requirements:

```bash
pip install -r requirements.txt
```

Change directories into the OpenFindIt folder

```bash
cd openfindit
```

## To search multiple domains for documents:

```bash
scrapy crawl findfiles -a filename=list-of-websites.txt  -s DEPTH_LIMIT=1 -t csv -o - > 'docs/assets/alice_today.csv'
```

## To search one domain for documents:

```bash
scrapy crawl findfiles -a urls=http://joelcrawfordsmith.com/openassessit/demo/test-pdf-links.html -s DEPTH_LIMIT=1 -o wiki-single-sites2.csv
```

## To search one domain for videos (NOTE: DEPTH_LIMIT must be 2 or greater to crawl video metadata):

You can use a url, a text file with a list of urls, or provide a sitemap.

For just crawling pages starting at a specific URL on non-ajaxy non-SPA websites use the following. Set the DEPTH_LIMIT to as deep as you want.

```bash
scrapy crawl findvideos -a urls=http://joelcrawfordsmith.com/openassessit/demo/test-index.html  -s DEPTH_LIMIT=5 -s CLOSESPIDER_PAGECOUNT=50000 -t csv -o - > 'docs/assets/find_videos.csv'
```

For just crawling a a single url or comma separted list of urls to use as starting pages in a on non-ajaxy non-SPA websites use the following. Set the DEPTH_LIMIT to as deep as you want.

```bash
scrapy crawl findvideos -a urls=http://joelcrawfordsmith.com/openassessit/demo/test-index.html  -s DEPTH_LIMIT=5 -s CLOSESPIDER_PAGECOUNT=50000 -t csv -o - > 'docs/assets/find_videos.csv'
```

For just crawling a list or urls in a text file as starting pages in a on non-ajaxy non-SPA websites use the following. Set the DEPTH_LIMIT to as deep as you want.

```bash
scrapy crawl findvideos -a filename=list-of-websites.txt -s DEPTH_LIMIT=5 -s CLOSESPIDER_PAGECOUNT=50000 -t csv -o - > 'docs/assets/find_videos.csv'
```

For ajaxy SPA websites, you must use a sitemap so it can find every page. Use DEPTH_LIMIT of 0, because all of the URLs are listed in the sitemap, therefore it does not need to crawl the webpage find the next webpage.

```bash
scrapy crawl findvideos -a sitemap_url="https://foo.edu/sitemap/sitemap-0.xml" -s DEPTH_LIMIT=0 -s CLOSESPIDER_PAGECOUNT=500000 -t csv -O results/oie_videos_2025.csv
```

`-a` is for passing in OpenFindIt arguments for which website(s) to scan.

`-s` is for passing any native built-in [Scapy settings](https://docs.scrapy.org/en/latest/topics/settings.html), like [DEPTH_LIMIT](https://docs.scrapy.org/en/latest/topics/settings.html#depth-limit) or [CLOSESPIDER_PAGECOUNT](https://docs.scrapy.org/en/latest/topics/settings.html#closespider_pagecount).

`-t` is for file type.

`-o` is for the name of your output file.
