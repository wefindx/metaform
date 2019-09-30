from datetime import datetime

from dateutil.parser import parse as dateparse

# TODO: refactor exceptions


def object(x, silent=True):
    # return dict(x)
    try:
        return dict(x)
    except Exception as e:
        if silent:
            return x
        else:
            raise e


def integer(x, silent=True):
    # return int(x)
    try:
        return int(x)
    except Exception as e:
        if silent:
            return x
        else:
            raise e


def decimal(x, silent=True):
    # return float(x)
    try:
        return float(x)
    except Exception as e:
        if silent:
            return x
        else:
            raise e


def rational(x, silent=True):
    # return float(x)
    try:
        return float(x)
    except Exception as e:
        if silent:
            return x
        else:
            raise e


def float(x, silent=True):
    # return float(x)
    try:
        return float(x)
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
        return dateparse(x)
    except Exception as e:
        if silent:
            return x
        else:
            raise e


def unixtime(x, silent=True):
    # return isoparse(x)
    try:
        return datetime.utcfromtimestamp(x)
    except Exception as e:
        if silent:
            return x
        else:
            raise e

#
# def url(x, silent=True):
#     # return urlparse(x)
#     try:
#         return urlparse(x)
#     except Exception as e:
#         if silent:
#             return x
#         else:
#             raise e


def imarkdown(x):
    return x
