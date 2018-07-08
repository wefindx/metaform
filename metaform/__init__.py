from boltons.iterutils import remap

from metaform.utils import (
    dictget,
    metapath,
    slug
)

# convenience alias #
from metaform.utils import metaplate #noqa



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

def normalize(data, schema, slugify=True, storage=None):
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
