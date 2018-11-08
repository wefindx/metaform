from boltons.iterutils import remap

from metaform.utils import (
    dictget,
    metapath,
    slug
)

# convenience alias #
from metaform.schema_readers import get_schema #noqa
from metaform.utils import metaplate #noqa
from metaform.utils import metaplate as template #noqa
from metaform.utils import get_concept
from metaform import converters


import requests, json

def convert(key, value, schema, slugify=False, storage=None):
    """
    Given a dictionary key, value, and schema specification,
    returns the key with normalize value.

    Optionally, saves the {slugified -> original} map in the storage.

    E.g.:
    Given:
    >>> schema = {
        '*': "https://www.wikidata.org/wiki/Q82799|lambda _: _.replace(',','')"
    }
    >>> convert(key='something', value='1,234', schema)
    ('https://www.wikidata.org/wiki/Q82799', '1234')
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

                # Save the slugified key.
                if storage:
                    try:
                        storage['types']['_terms'].insert(record)
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

def normalize(data, schema=None, slugify=True, storage=None):
    '''
    Combine data with schema and types in schema by zipping tree.

    Example:
    >>> data = \
    [{'name': 'max',
      'age': {'median': 21, 'average': 30}},
     {'name': 'min',
      'age': {'median': 12, 'average': 15}}]
    >>> schema = \
    [{'*': 'https://www.wikidata.org/wiki/Q7565',
    'name': {'*': 'https://www.wikidata.org/wiki/Q82799|lambda _: _.title()'},
    'age': {
        '*': 'https://www.wikidata.org/wiki/Q185836',
        'median': {'*': 'https://www.wikidata.org/wiki/Q185836#median'},
        'average': {'*': 'https://www.wikidata.org/wiki/Q185836#average'}}}]
    >>> normalize(data, schema)
    [{'https-www-wikidata-org-wiki-q82799': 'Max',
      'https-www-wikidata-org-wiki-q185836':
         {'https-www-wikidata-org-wiki-q185836#median': 21,
          'https-www-wikidata-org-wiki-q185836#average': 30}},
     {'https-www-wikidata-org-wiki-q82799': 'Min',
      'https-www-wikidata-org-wiki-q185836':
         {'https-www-wikidata-org-wiki-q185836#median': 12,
          'https-www-wikidata-org-wiki-q185836#average': 15}}]
    '''
    if not schema:
        if '*' in data.keys():
            schema = get_schema(data['*'])

    def visit(path, key, value):
        try:
            # Gets the path schema at this dictionary level
            meta = dictget(schema, metapath(path))[key if not isinstance(key, int) else 0]
            if isinstance(meta, list):
                meta = meta[0]
            return convert(key, value, meta, slugify=slugify, storage=storage)
        except:
            return key, value

    remapped = remap(data, visit=visit)

    return remapped

def translate(ndata, lang=None, refresh=False):
    '''
    Applies language conversion if available to the keys.

    For example, based on metawiki, '_:date' is an a term,
    namely: https://github.com/infamily/indb/wiki/date

    And it has aliases in other languages. Translate takes
    the first alias, and uses it to represent the key.
    '''

    if lang:
        def visit(path, key, value):
            concept = get_concept(key, refresh)

            if concept:
                if concept.get('aliases'):
                    if concept['aliases'].get(lang):
                        return concept['aliases'][lang][0], value

            return key, value

        return remap(ndata, visit=visit)

    else:
        return ndata

def formatize(ndata, ignore=[]):
    '''
    Applies converters, if they match the name after hash.

    For example, if the key is '_:date#isoformat', then the
    converters.isoformat() is applied to the value, if exists.

    It returns keys without the # sign.
    '''

    def visit(path, key, value):

        if isinstance(key, str):
            if '#' in str(key)[1:-1:]:
                if type(value) in [str, int, float]:
                    if hasattr(converters, key.rsplit('#', 1)[-1]):
                        k = key.rsplit('#', 1)[0]
                        v = getattr(converters, key.rsplit('#', 1)[-1])(value)
                        if (k in ignore) or (key in ignore):
                            return k, value
                        return k, v

                return key.rsplit('#', 1)[0], value

        return key, value

    result = remap(ndata, visit=visit)

    if isinstance(ndata, list):
        result = List(result)

    return result


class Dict(dict):

    def format(self, lang=None, refresh=False):
        if lang:
            return translate(formatize(normalize(self)), lang=lang, refresh=refresh)

        return formatize(normalize(self))

    def render(self, lang, refresh=False):
        return translate(normalize(self), lang=lang, refresh=refresh)


class List(list):

    def format(self, lang=None, refresh=False):
        if lang:
            return translate(formatize([normalize(item) for item in self]), lang=lang, refresh=refresh)

        return formatize([normalize(item) for item in self])

    def render(self, lang, refresh=False):
        return translate([normalize(item) for item in self], lang=lang, refresh=refresh)


def load(data):

    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        records = data
    elif data.startswith('http'):
        records = requests.get(data).json()
    else:
        records = json.load(open(data))

    if isinstance(records, list):
        ndata = List([Dict(item) for item in records])
    elif isinstance(records, dict):
        ndata = Dict(records)

    return ndata
