from scrapy.utils.httpobj import urlparse
from urllib.parse import urlparse, parse_qs

def get_id(url):
    """ parse YouTube urls for id """
    u_pars = urlparse(url)
    quer_v = parse_qs(u_pars.query).get('v')
    if quer_v:
        return quer_v[0]
    pth = u_pars.path.split('/')
    if pth:
        return pth[-1]


def cc_status(cc):
    """ parse for captions """
    if "Available subtitles for" in cc:
        yield "YES"
    elif "has no subtitles" in cc:
        yield "NO"
    elif "video doesn't have subtitles" in cc:
        yield "NO"
    else:
        yield "UNKNOWN"  