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
from copy import deepcopy

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

def getx(data, path, inany=False):
    if not inany:
        try:
            return dictget(data, path)
        except:
            return None
    else:
        oneup = dictget(data, path[:-1])
        if isinstance(oneup, list):
            possible_paths = [path[:-1]+(i,)+path[-1:] for i in range(len(oneup))]
            for p in possible_paths:
                try:
                    item = dictget(data, p)
                    break
                except:
                    item = None
            if item is not None:
                return p, item
            else:
                return None

def setx(data, path, value, other):
    '''
    Example:
    >>> setx({'a': 1, 'b': 2}, ['c', 0, 'd'], 8, {'c': [{'d': 12}]})
    {'a': 1, 'b': 2, 'c': [{'d': 8}]}
    '''
    r = data
    i = []
    for p in path[:-1]:
        i += [p]

        if (isinstance(r, dict) and (p not in r.keys())) or \
           (isinstance(r, list) and (p not in range(len(r)))):
            try:
                other_type = type(getx(other, i)) # [], {}
            except:
                other_type = dict

            if isinstance(r, dict):
                r[p] = other_type()
            elif isinstance(r, list):
                r += [other_type()]
            else:
                print('hmm')

        r = r[p]

    try:
        r[path[-1]] = value
    except:
        # do nothing #
        pass

    return data

def _add(a, b):
    a = deepcopy(a)
    def visit(path, key, value):
        fpath = path + (key,)
        val = getx(a, fpath)

        if val is not None:
            if type(val) != type(value):
                new_val = [val, value]
            elif hasattr(val, '__add__'):
                new_val = val + value
            else:
                new_val = [val, value]
            setx(a, fpath, new_val, b)
        else:
            setx(a, fpath, value, b)

        return key, value

    sink = remap(b, visit=visit)
    return a


def delx(data, path):
    '''
    >>> delx({'a': 3, 'b': [2, {'x': 'y'}], 'c': 3, 'd': 4}, ['b', 1, 'x'])
    {'a': 3, 'b': [2, {}], 'c': 3, 'd': 4}
    >>> delx({'a': 3, 'b': [2, {'x': 'y'}], 'c': 3, 'd': 4}, ['b', 0])
    '''
    # data = deepcopy(data)

    r = data
    for p in path[:-1]:
        r = r[p]
    del r[path[-1]]
    if not r:
        del r

    return data


def _sub(a, b):
    '''
    >>> _sub({'a': 3, 'b': [2, {'x': 'y'}], 'c': 3, 'd': 4},
             {'a': 2, 'b': {'x': 'y'}, 'c': 3, 'd': 4})

    {'a': 1, 'b': 2}
    '''
    a = deepcopy(a)
    a['___previous_was_list___'] = False
    def visit(path, key, value):
        fpath = path + (key,)
        vala = getx(a, fpath)
        valb = value

        if isinstance(getx(a, fpath[:-1]), list):
            valA = getx(a, fpath, inany=True)
        else:
            valA = None

        if vala is not None:
            if type(vala) != type(valb):
                if not isinstance(vala, list):
                    vala = [vala]
                if not isinstance(valb, list):
                    valb = [valb]
                new_val = [v for v in vala if v in valb]
                if len(new_val) == 1:
                    new_val = new_val[0]
                if not a['___previous_was_list___']:
                    setx(a, fpath, new_val, b)
                a['___previous_was_list___'] = False
                #print('>>', a, (vala, valb))
            elif hasattr(vala, '__sub__'):
                new_val = vala - valb
                if not a['___previous_was_list___']:
                    if new_val:
                        setx(a, fpath, new_val, b)
                    else:
                        delx(a, fpath)

        else:
            if valA is not None:
                #print(valA)
                npath, _ = valA
                #print('->', a)
                delx(a, npath[:-1])
                #print('-<', a)
                a['___previous_was_list___'] = True


        return key, value

    sink = remap(b, visit=visit)
    del a['___previous_was_list___']
    return a
