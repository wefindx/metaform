from boltons.iterutils import remap
from functools import reduce
import operator

from slugify import slugify
from pymongo import MongoClient # store slugs

from . import converters

client = MongoClient()

def slug(url):
    if '#' in url:
        url, anchor = url.rsplit('#', 1)
        return '{}#{}'.format(slugify(url), slugify(anchor))
    else:
        return slugify(url)

def convert(key, value, schema, slugify=False):
    """
    Given:
    >>> key = 'something'
    >>> value = '1,234'
    >>> schema = {'*': "https://www.wikidata.org/wiki/Q82799|lambda _: _.replace(',','')"}

    Returns:
    >>> key = 'https://www.wikidata.org/wiki/Q82799'
    >>> value = 1234
    """

    if not isinstance(schema, dict):
        # schema can't ba non-dict
        return key, value

    if '*' not in schema.keys():
        # bad schema
        return key, value

    schema = schema.get('*')

    if schema:

        if '|' not in schema:
            schema+='|'

        term, rules = schema.split('|')

        if term:

            if slugify:
                record = {'name': slug(term), 'url': term}
                try:
                    client['types']['_terms'].insert(record)
                except:
                    # Probaby, already exists.
                    pass
                term = record['name']

        if rules:
            try:
                value = eval(rules)(value)
            except Exception as e:
                if not any([isinstance(value, t) for t in [list, tuple, dict]]):
                    print('Failed to convert value: {}'.format(value))
                    print(e)
                pass

        if term:
            key = term

    return key, value


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


def normalize(data, schema, slugify=True):
    '''
    Combine data with schema and types in schema by zipping tree.
    Given:
    >>> data = \
    [{'address': {'number': 14, 'street': 'Leonardo str.'},
     'children': [{'age': 1, 'name': 'Mike'}, {'age': 15, 'name': 'Tom'}],
     'name': 'Max'},
    {'address': {'number': 12, 'street': 'Mao str.'},
     'children': [{'age': 10, 'name': 'Sonnie'}],
     'name': 'Lin'},
    {'address': {'number': 1, 'street': 'Nexus str.'},
     'children': [{'age': 1, 'name': 'Deli'}, {'age': 7, 'name': 'Miki'}],
     'name': 'Dim'}]
    >>> schema = \
    [{'*': 'https://www.wikidata.org/wiki/Q7565',
    'address': {'*': 'https://www.wikidata.org/wiki/Q319608',
     'number': {'*': 'https://www.wikidata.org/wiki/Q1413235|lambda _: int(_)'},
     'street': {'*': 'https://www.wikidata.org/wiki/Q24574749'}},
    'children': [{'*': 'https://www.wikidata.org/wiki/Q7569',
      'age': {'*': 'https://www.wikidata.org/wiki/Q185836|lambda _: float(_)'},
      'name': {'*': 'https://www.wikidata.org/wiki/Q82799'}}],
    'name': {'*': 'https://www.wikidata.org/wiki/Q82799'}}]
    >>> normalize(data, schema)
    [{'https-www-wikidata-org-wiki-q319608': {'https-www-wikidata-org-wiki-q1413235': 14,
       'https-www-wikidata-org-wiki-q24574749': 'Leonardo str.'},
      'https-www-wikidata-org-wiki-q7569': [{'https-www-wikidata-org-wiki-q185836': 1.0,
        'https-www-wikidata-org-wiki-q82799': 'Mike'},
       {'https-www-wikidata-org-wiki-q185836': 15.0,
        'https-www-wikidata-org-wiki-q82799': 'Tom'}],
      'https-www-wikidata-org-wiki-q82799': 'Max'},
     {'https-www-wikidata-org-wiki-q319608': {'https-www-wikidata-org-wiki-q1413235': 12,
       'https-www-wikidata-org-wiki-q24574749': 'Mao str.'},
      'https-www-wikidata-org-wiki-q7569': [{'https-www-wikidata-org-wiki-q185836': 10.0,
        'https-www-wikidata-org-wiki-q82799': 'Sonnie'}],
      'https-www-wikidata-org-wiki-q82799': 'Lin'},
     {'https-www-wikidata-org-wiki-q319608': {'https-www-wikidata-org-wiki-q1413235': 1,
       'https-www-wikidata-org-wiki-q24574749': 'Nexus str.'},
      'https-www-wikidata-org-wiki-q7569': [{'https-www-wikidata-org-wiki-q185836': 1.0,
        'https-www-wikidata-org-wiki-q82799': 'Deli'},
       {'https-www-wikidata-org-wiki-q185836': 7.0,
        'https-www-wikidata-org-wiki-q82799': 'Miki'}],
      'https-www-wikidata-org-wiki-q82799': 'Dim'}]

    # There is a problem with nested still have "children" in keys.
    '''

    def visit(path, key, value):
        try:
            # Gets the path schema at this dictionary level
            meta = dictget(schema, metapath(path))[key if not isinstance(key, int) else 0]
            if isinstance(meta, list):
                meta = meta[0]
            return convert(key, value, meta, slugify=slugify)
        except:
            return key, value

    remapped = remap(data, visit=visit)

    return remapped


def get_keypaths(data):
    '''
    Get a list of json paths in a json-like dict-list.

    (which can be used with dictget())
    '''
    paths = []
    def visit(path, key, value):
        paths.append(path)
        return None, None
    null = remap(data, visit=visit)
    return paths


def get_keymap(data1, data2):
    '''
    If dictionaries are homomorphic, return the hierarchically zipped key map.

    data1 = \
  [{'address': {'number': 14, 'street': 'Leonardo str.'},
  'children': [{'age': 1, 'name': 'Mike'}, {'age': 15, 'name': 'Tom'}],
  'name': 'Max'},
 {'address': {'number': 12, 'street': 'Mao str.'},
  'children': [{'age': 10, 'name': 'Sonnie'}],
  'name': 'Lin'},
 {'address': {'number': 1, 'street': 'Nexus str.'},
  'children': [{'age': 1, 'name': 'Deli'}, {'age': 7, 'name': 'Miki'}],
  'name': 'Dim'}]

    data2 = \
  [{'https-www-wikidata-org-wiki-q319608': {'https-www-wikidata-org-wiki-q1413235': 14,
   'https-www-wikidata-org-wiki-q24574749': 'Leonardo str.'},
  'https-www-wikidata-org-wiki-q7569': [{'https-www-wikidata-org-wiki-q185836': 1.0,
    'https-www-wikidata-org-wiki-q82799': 'Mike'},
   {'https-www-wikidata-org-wiki-q185836': 15.0,
    'https-www-wikidata-org-wiki-q82799': 'Tom'}],
  'https-www-wikidata-org-wiki-q82799': 'Max'},
 {'https-www-wikidata-org-wiki-q319608': {'https-www-wikidata-org-wiki-q1413235': 12,
   'https-www-wikidata-org-wiki-q24574749': 'Mao str.'},
  'https-www-wikidata-org-wiki-q7569': [{'https-www-wikidata-org-wiki-q185836': 10.0,
    'https-www-wikidata-org-wiki-q82799': 'Sonnie'}],
  'https-www-wikidata-org-wiki-q82799': 'Lin'},
 {'https-www-wikidata-org-wiki-q319608': {'https-www-wikidata-org-wiki-q1413235': 1,
   'https-www-wikidata-org-wiki-q24574749': 'Nexus str.'},
  'https-www-wikidata-org-wiki-q7569': [{'https-www-wikidata-org-wiki-q185836': 1.0,
    'https-www-wikidata-org-wiki-q82799': 'Deli'},
   {'https-www-wikidata-org-wiki-q185836': 7.0,
    'https-www-wikidata-org-wiki-q82799': 'Miki'}],
  'https-www-wikidata-org-wiki-q82799': 'Dim'}]

    get_keymap(data1, data2)
    {(0, 'address'): (0, 'https-www-wikidata-org-wiki-q319608'),
     (0,): (0,),
     (0, 'children', 0): (0, 'https-www-wikidata-org-wiki-q7569', 0),
     (0, 'children'): (0, 'https-www-wikidata-org-wiki-q7569'),
     (0, 'children', 1): (0, 'https-www-wikidata-org-wiki-q7569', 1),
     (): (),
     (1, 'address'): (1, 'https-www-wikidata-org-wiki-q319608'),
     (1,): (1,),
     (1, 'children', 0): (1, 'https-www-wikidata-org-wiki-q7569', 0),
     (1, 'children'): (1, 'https-www-wikidata-org-wiki-q7569'),
     (2, 'address'): (2, 'https-www-wikidata-org-wiki-q319608'),
     (2,): (2,),
     (2, 'children', 0): (2, 'https-www-wikidata-org-wiki-q7569', 0),
     (2, 'children'): (2, 'https-www-wikidata-org-wiki-q7569'),
     (2, 'children', 1): (2, 'https-www-wikidata-org-wiki-q7569', 1)}

    so that we can:

    dictget(data1, (0, 'address'))
    {'number': 14, 'street': 'Leonardo str.'}

    dictget(data2, get_keymap(data1, data2)[(0, 'address')])
    {'https-www-wikidata-org-wiki-q1413235': 14,
 'https-www-wikidata-org-wiki-q24574749': 'Leonardo str.'}
    '''

    paths1 = get_keypaths(data1)
    paths2 = get_keypaths(data2)

    return dict(zip(paths1, paths2))


def rename_keys(data, keymap):
    '''
    data = {
        'hello': {
            'world': 1
            }
    }
    keymap = {('hello','world'): ('one', 'world')}

    Result:
    {
        'one': {
            'world': 1
            }
    }
    '''
    def visit(path, key, value):
        if path in keymap.keys():
            return keymap[path][-1], value
        else:
            return key, value
    result = remap(data, visit=visit)

    return result



def keypath_to_query(keypath, value):
    '''
    Given:
    path = ('hello', 1, 'world')
    value = 'nice'

    Returns:
    {'hello.1.world': 'nice'}
    '''
    keypath = [str(token) for token in keypath]
    return {'.'.join(keypath): value}


def keypath_query_to_query(query):
    '''
    Given:
    query = {
        ('hello', 1, 'world'): 'test',
        ('nice',): 1,
    }

    Returns:
    {'hello.1.world': 'test', 'nice': 1}
    '''
    result = {}
    for (key, value) in query.items():
        result.update(keypath_to_query(key, value))
    return result


def leave_only_these_keys(data, keys):
    '''
    Given:
    data = {
        'a': 'test',
        'b': 1,
    }
    paths = ['a']

    Returns:

    {
        'b': 1,
    }
    '''

    for key in set(data.keys())-set(paths):
        del data[key]
    return data
