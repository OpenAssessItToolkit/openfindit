# OpenFindIt (Work in Progress)

This is a little [Scrapy](https://github.com/scrapy/scrapy) script to find documents on a website and send them to a CSV.

Scrapy is infinitely configurable. This specific crawler implementation features:

- Filters out documents hosted on other domains.
- Uses a slow crawling speed to avoid putting a big load on the server.

You can use it as-is or use it as a template to create your own.

Make sure you have permission to scan the website!

__Prerequisites:__

1. [Start up a virtual environment](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)

2. Install requirements:

```bash
pip install -r requirements.txt
```

## Using OpenFindIt:

Change directories into the OpenFindIt folder

```bash
cd openfindit
```


### To search one domain:

```bash
scrapy crawl findfiles -a urls=https://somewebsite.com -s DEPTH_LIMIT=1 -o wiki-single-sites2.csv
```

### To search multiple domains:

```bash
scrapy crawl findfiles -a filename=list-of-websites.txt  -s DEPTH_LIMIT=1 -o list-of-websites.csv
```


`-a` is for passing in OpenFindIt arguments for which website(s) to scan

`-s` is for passing in any native built-in [Scapy settings](https://docs.scrapy.org/en/latest/topics/settings.html), like [DEPTH_LIMIT](https://docs.scrapy.org/en/latest/topics/settings.html#depth-limit).

`-o` is for the name of your output file.
