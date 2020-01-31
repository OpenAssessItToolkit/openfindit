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

```bash
scrapy crawl findvideos -a urls=http://joelcrawfordsmith.com/openassessit/demo/test-index.html  -s DEPTH_LIMIT=5 -s CLOSESPIDER_PAGECOUNT=500 -t csv -o - > 'docs/assets/find_videos.csv'
```


`-a` is for passing in OpenFindIt arguments for which website(s) to scan.

`-s` is for passing any native built-in [Scapy settings](https://docs.scrapy.org/en/latest/topics/settings.html), like [DEPTH_LIMIT](https://docs.scrapy.org/en/latest/topics/settings.html#depth-limit) or [CLOSESPIDER_PAGECOUNT](https://docs.scrapy.org/en/latest/topics/settings.html#closespider_pagecount).

`-t` is for file type.

`-o` is for the name of your output file.
