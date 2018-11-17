import os
import pathlib
from boltons.iterutils import remap
from slugify import slugify
from functools import reduce
import operator
from tinydb import TinyDB, Query

from . import converters

import metawiki
import typology
from collections import defaultdict

conf_path = os.path.join( str(pathlib.Path.home()), '.ooio')

if not os.path.exists(conf_path):
    os.makedirs(conf_path)

db = TinyDB(os.path.join(conf_path, 'db.json'))


def slug(url, skip_valid=True):

    if skip_valid:
        if metawiki.isname(url):
            return url

    # exception
    if url == '-':
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
    if isinstance(data, list):
        # TODO: reserved key
        data = {'_#list#_': data}

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

    remapped = remap(data, visit=visit)

    if with_self:
        if isinstance(remapped, dict):
            remapped.update({'*': ''})
        elif isinstance(remapped, list):
            if remapped:
                if remapped[0]:
                    remapped[0].update({'*': ''})


    if '_#list#_' in remapped.keys():
        remapped = remapped['_#list#_']

    return remapped


def get_concept(value, refresh=False):

    if any(
        [str(value).startswith(it) for it in
         list(metawiki.NAMESPACES.keys()) + ['https://github.com', 'https://www.wikidata.org']]
    ):

        Concept = Query()

        url = metawiki.name_to_url(str(value))
        slg = slug(url)

        result = db.search(Concept.slug == slg)

        if refresh or not result:

            try:
                concept = typology.Concept(url).concept
                result = {'slug': slg, 'concept': concept}
                db.insert(result)

                return concept

            except:
                print("-> Undefined concept: {}".format(url))

        elif result:
            return result[0]['concept']
    else:
        return


def get_concept_paths(data, k=[], exclude=[dict, list]):
    '''
    Given, something like:
    >>> get_concept_paths({'a': {'b': [{'c': 1}]}, 'x': {'c': 2}}, 'c')

    Returns a list of paths, where given concept ('c') is
    >>> [['a', 'b', 0, 'c'], ['x', 'c']] # = p

    So that we can retrieve them with dictget()
    '''

    if isinstance(k, list):
        paths = {key: [] for key in k}
    else:
        paths = []

    if not k:
        paths = defaultdict(list)

    def visit(path, key, value):
        if isinstance(k, list):
            if key in k or not k:
                if type(value) not in exclude:
                    paths[key].append(list(path) + [key])
        else:
            if key == k or not k:
                if type(value) not in exclude:
                    paths.append(list(path) + [key])
        return key, value

    remap(data, visit=visit)

    return paths


def get_match_matrix(
        source_schema_list, exclude=[dict, list]):
    '''
    Given a few sourcemetaform.utils.match_sources([ {'a': {'c': 'X'}, 'n': 1}, {'b': {'a': {'c': 'Y'}}, 'd': {'n': 2}} ])metaform.utils.match_sources([ {'a': {'c': 'X'}, 'n': 1}, {'b': {'a': {'c': 'Y'}}, 'd': {'n': 2}} ])metaform.utils.match_sources([ {'a': {'c': 'X'}, 'n': 1}, {'b': {'a': {'c': 'Y'}}, 'd': {'n': 2}} ]) schemas, e.g.
    >>> get_matche_matrix([{'a': {'b': 'X'}, 'n': 1}, {'b': {'a': {'c': 'Y'}}, 'd': {'n': 2}}])

    >>> {'n': [['n'], ['d', 'n']]}
    >>> metaform.utils.get_match_matrix([ {'a': {'c': 'X'}, 'n': 1}, {'b': {'a': {'c': 'Y'}}, 'd': {'n': 2}} ])
    >>>

    Returns found matching keys, that can be merged.
    '''

    field_availability_list = [
        get_concept_paths(source, exclude=exclude)
        for source in source_schema_list
    ]

    common_field_set = set.intersection(*map(set, field_availability_list))

    match = {}
    for field in common_field_set:
        lists = []
        for source in field_availability_list:
            lists.append(source[field][0])
        match[field] = lists

    return match


def match(dict_list, exclude=[dict, list]):

    results = {}

    matches = get_match_matrix(dict_list, exclude=exclude)

    for key in matches:
        results.update(
            {key: [dictget(source, matches[key][i])
             for i, source in enumerate(dict_list)]})

    return results
