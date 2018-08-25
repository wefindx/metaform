from boltons.timeutils import isoparse
from urllib.parse import urlparse
from decimal import Decimal
import langsplit

# TODO: refactor exceptions

def object(x):
    # return dict(x)
    try:
        return dict(x)
    except Exception as e:
        if silent:
            return x
        else:
            raise e

def integer(x, silent=True):
    #return int(x)
    try:
        return int(x)
    except Exception as e:
        if silent:
            return x
        else:
            raise e

def rational(x, silent=True):
    #return float(x)
    try:
        return float(x)
    except Exception as e:
        if silent:
            return x
        else:
            raise e

def decimal(x, silent=True):
    #return decimal(x)
    try:
        return Decimal(x)
    except Exception as e:
        if silent:
            return x
        else:
            raise e

def string(x, silent=True):
    # return str(x)
    try:
        return str(x)
    except Exception as e:
        if silent:
            return x
        else:
            raise e

def isodate(x, silent=True):
    # return isoparse(x)
    try:
        return isoparse(x)
    except Exception as e:
        if silent:
            return x
        else:
            raise e

def url(x, silent=True):
    # return urlparse(x)
    try:
        return urlparse(x)
    except Exception as e:
        if silent:
            return x
        else:
            raise e

def imarkdown(x):
    return x
