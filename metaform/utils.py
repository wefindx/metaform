from boltons.iterutils import remap
from slugify import slugify
from functools import reduce
import operator
from . import converters

import metawiki


def slug(url, skip_valid=True):

    if skip_valid:
        if metawiki.isname(url):
            return url

    if '#' in url:
        url, anchor = url.rsplit('#', 1)
        return '{}#{}'.format(slugify(url), slugify(anchor))
    else:
        return slugify(url)

def dictget(d, mapList):
    '''
    Given:
    >>> d = {'a': [{'b': 'c'}, {'e': 'f'}, {'g': 'h'}]}
    Returns:
    >>> dictget(d, ['a', 2, 'b'])
    >>> 'c'
    '''
    return reduce(operator.getitem, mapList, d)

def metapath(path):
    '''
    Given:
    >>> p = [1, 'a', 2, 'b', 3]
    Returns:
    >>> metapath(p)
    >>> [0, 'a', 0, 'b', 0]
    '''
    metapath = []
    for item in path:
        if isinstance(item, int):
            metapath.append(0)
        else:
            metapath.append(item)
    return metapath

def metaplate(data, with_self=True):
    '''
    Creates a meta-template for a dictionary-like data.

    Given:
    >>> data = {'a': [{'b': 'c'}, {'e': 'f'}, {'g': 'h'}], 'b': 'something'}

    Returns template:
    >>> metaplate(data) == result
    result = {
        '*': '',
        'a': [
            {'*': '',
             'b': {'*': ''},
             'e': {'*': ''},
             'g': {'*': ''}}
        ],
        'b': {'*': ''}
    }
    '''
    # helpers:
    def sum_dicts(list_of_dicts):
        result = {}
        for item in list_of_dicts:
            if isinstance(item, dict):
                result.update(item)
        return [result]

    def visit(path, key, value):
        if isinstance(value, list):
            combined = sum_dicts(value)
            combined[0].update({'*': ''})
            return key, combined
        if not isinstance(value, list) and not isinstance(value, dict):
            return key, {'*': ''}
        else:
            return key, value

    # def schematize(obj):
    #     if isinstance(obj, dict):
    #         return {k: schematize(v) for k, v in obj.items()}
    #     elif isinstance(obj, list):
    #         return sum_dicts([schematize(elem) for elem in obj])
    #     else:
    #         return obj

    # data = schematize(data)

    remapped = remap(data, visit=visit)

    if with_self:
        if isinstance(remapped, dict):
            remapped.update({'*': ''})
        elif isinstance(remapped, list):
            if remapped:
                if remapped[0]:
                    remapped[0].update({'*': ''})

    return remapped
