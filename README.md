# OpenFindIt (Work in Progress)

This is a little [Scrapy](https://github.com/scrapy/scrapy) script to find documents on a website and send them to a CSV.

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


## To search one domain:

```bash
scrapy crawl findfiles -a urls=http://joelcrawfordsmith.com/openassessit/demo/test-pdf-links.html -s DEPTH_LIMIT=1 -o wiki-single-sites2.csv
```

## To search multiple domains:

```bash
scrapy crawl findfiles -a filename=list-of-websites.txt  -s DEPTH_LIMIT=1 -t csv -o - > 'docs/assets/alice_today.csv'
```


`-a` is for passing in OpenFindIt arguments for which website(s) to scan.

`-s` is for passing some native built-in [Scapy settings](https://docs.scrapy.org/en/latest/topics/settings.html), like [DEPTH_LIMIT](https://docs.scrapy.org/en/latest/topics/settings.html#depth-limit).

`-t` is for file type.

`-o - >` is for the name of your output file and directs it to overwrite the current file, rather than append.
