from boltons.iterutils import remap

from metaform.utils import (
    dictget,
    metapath,
    slug
)


def convert(key, value, schema, slugify=False, storage=None):
    """
    Given a dictionary key, value, and schema specification,
    returns the key with normalize value.

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

def normalize(data, schema, slugify=True):
    '''
    Combine data with schema and types in schema by zipping tree.
    Given:
    >>> data = \
    [{'address': {'number': 14, 'street': 'Leonardo str.'},
     'children': [{'age': 1, 'name': 'Mike'}, {'age': 15, 'name': 'Tom'}],
     'name': 'Max'},
    {'address': {'number': 1, 'street': 'Nexus str.'},
     'children': [{'age': 1, 'name': 'Deli'}, {'age': 7, 'name': 'Miki'}],
     'name': 'Dim'}]
    >>> schema = \
    [{'_version': 'domain.com/parents-0.1',
    '*': 'https://www.wikidata.org/wiki/Q7565',
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
     {'https-www-wikidata-org-wiki-q319608': {'https-www-wikidata-org-wiki-q1413235': 1,
       'https-www-wikidata-org-wiki-q24574749': 'Nexus str.'},
      'https-www-wikidata-org-wiki-q7569': [{'https-www-wikidata-org-wiki-q185836': 1.0,
        'https-www-wikidata-org-wiki-q82799': 'Deli'},
       {'https-www-wikidata-org-wiki-q185836': 7.0,
        'https-www-wikidata-org-wiki-q82799': 'Miki'}],
      'https-www-wikidata-org-wiki-q82799': 'Dim'}]

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
