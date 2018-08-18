from boltons.timeutils import isoparse
from urllib.parse import urlparse
from decimal import Decimal

def object(x):
    return dict(x)

def integer(x):
    return int(x)

def rational(x):
    return float(x)

def decimal(x):
    return decimal(x)

def string(x):
    return str(x)

def isodate(x):
    return isoparse(x)

def url(x):
    return urlparse(x)
