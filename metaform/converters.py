from boltons.timeutils import isoparse
from urllib.parse import urlparse

def object(x):
    return dict(x)

def string(x):
    return str(x)

def isodate(x):
    return isoparse(x)

def url(x):
    return urlparse(x)
