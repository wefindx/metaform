import importlib
import json, yaml
import os

import metawiki
import requests
from boltons.iterutils import remap
from metaform import converters
# convenience alias #
from metaform.utils import _add, _sub, dictget, get_concept, get_match_matrix, get_schema, metapath
from metaform.utils import metaplate as template  # noqa
from metaform.utils import slug

to = converters


def convert(key, value, schema, slugify=False, namespace=False, storage=None):
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
    >>> convert(key='something', value='1,234', schema, name=True)
    ('WD:Q82799', '1234')
    """

    if not isinstance(schema, dict) and not isinstance(schema, str):
        # schema must be a dict or str
        return key, value
    #
    # if '*' not in schema.keys():
    #     # bad schema
    #     return key, value

    if isinstance(schema, dict):

        if '*' not in schema.keys():
            # bad schema
            return key, value

        schema = schema.get('*')

    if schema:

        if '|' not in schema:
            schema += '|'

        term, rules = schema.split('|')

        if term:
            if namespace:
                term = metawiki.url_to_name(term)

            if slugify:
                record = {'name': slug(term), 'url': term}

                # Save the slugified key.
                if storage:
                    try:
                        storage['types']['_terms'].insert(record)
                    except BaseException:
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


def normalize(data, schema=None, slugify=False, namespace=False, storage=None, refresh=False):
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
    if not schema or refresh:
        if '*' in data.keys():
            schema = get_schema(data['*'], refresh=refresh)

    def visit(path, key, value):
        try:
            # Gets the path schema at this dictionary level
            meta = dictget(schema, metapath(path))[key if not isinstance(key, int) else 0]
            if isinstance(meta, list):
                meta = meta[0]
            return convert(key, value, meta, slugify=slugify, namespace=namespace, storage=storage)
        except BaseException:
            return key, value

    remapped = remap(data, visit=visit)
    if isinstance(remapped, dict) and schema.get('*') in remapped:
        remapped['*'] = remapped.pop(schema.get('*'))
        remapped['*'] = schema.get('*')

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


def formatize(ndata, ignore=[], no_convert=[]):
    '''
    Applies converters, if they match the name after hash.

    For example, if the key is '_:date#isoformat', then the
    converters.isoformat() is applied to the value, if exists.

    It returns keys without the # sign.

    no_convert: list of types, not to apply conversion, e.g., ['url', 'decimal']
    '''

    def visit(path, key, value):

        if isinstance(key, str):
            if '#' in str(key)[1:-1:]:
                if type(value) in [str, int, float]:
                    Format = key.rsplit('#', 1)[-1]
                    if hasattr(converters, Format) and Format not in no_convert:
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

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def format(self, schema=None, lang=None, refresh=False, anchors=True):

        if isinstance(schema, str) and len(schema) <= 3:
            lang = schema
            schema = None

        if lang:
            return translate(formatize(normalize(self, schema=schema), no_convert=['url']), lang=lang, refresh=refresh)

        if anchors:
            return normalize(self, schema=schema, refresh=refresh)
        else:
            return formatize(normalize(self, schema=schema, refresh=refresh))

    def render(self, lang, schema=None, refresh=False):
        return translate(normalize(self, schema=schema), lang=lang, refresh=refresh)

    def __add__(self, other):
        return _add(self, other)

    def __sub__(self, other):
        return _sub(self, other)

    def start(self):
        ''' Initialize methods.
        TODO: To automate in __init__ later. '''

        url = self.get('-')
        schema = get_schema(self['*'])
        concept = metawiki.url_to_name(self['*'])
        # service_label = concept.rsplit('#', 1)[-1]
        class_name = concept.rsplit('/', 1)[-1].split('#', 1)[0].title()

        if '_:emitter' in schema.keys():
            if schema['_:emitter'].startswith('PyPI:'):

                from metadrive.utils import ensure_driver_installed
                ensure_driver_installed(schema['_:emitter'])

                # service_name = schema['_:emitter'][5:].rsplit('.', 1)[-1]
                module_name = schema['_:emitter'][5:].rsplit('.', 1)[0]

                # from [module_name].[api] import class_name
                api = importlib.import_module(
                    '{module_name}.api'.format(
                        module_name=module_name))

                # Map actions to interface.
                Klass = getattr(api, class_name)

                # # from [service_name] import login
                if self.get('+'):
                    service = importlib.import_module(
                        '{module_name}'.format(
                            module_name=module_name))

                    login = getattr(service, 'login')
                    session = login()
                    interface = Klass(url, session)

                    print('SUCCESSFULLY LOGGED IN')
                    # mapping interface from instance
                    for action in dir(interface):
                        if not action.startswith('__'):
                            setattr(self, action, getattr(interface, action))

                else:
                    interface = None

                    print('COULD NOT LOGIN')

                    # mapping interface from class
                    for action in Klass.__dict__:
                        if not action.startswith('__'):
                            setattr(self, action, Klass.__dict__[action])


class List(list):

    def format(self, schema=None, lang=None, refresh=False, anchors=True):

        if isinstance(schema, str) and len(schema) <= 3:
            lang = schema
            schema = None

        if lang:
            return translate(formatize([normalize(item, schema=schema)
                                        for item in self], no_convert=['url']), lang=lang, refresh=refresh)

        if anchors:
            return [normalize(item, schema=schema, refresh=refresh) for item in self]
        else:
            return formatize([normalize(item, schema=schema, refresh=refresh) for item in self])

    def render(self, lang, schema=None, refresh=False):
        return translate([normalize(item, schema=schema) for item in self], lang=lang, refresh=refresh)

    def normalize(self, refresh=False, by_record=0):
        schema_name = self[by_record].get('*')
        schema = get_schema(schema_name)
        return [normalize(item, schema=schema) for item in self]


def wrap(records: list, schema: dict):
    '''
    #records = [dict(row) for row in csv.DictReader(open('sample1.csv'))]
    #schema = metaform.get_schema('https://github.com/mindey/-/wiki/something#sample1')
    '''
    return List([Dict(record) for record in normalize(records, [schema])])


def load(data, schema=None):
    '''
    Reads data source, where each record has '*' attribute.

    Examples:
    >>> load('https://gist.github.com/mindey/2cdeecddab20d036b957cd0d306b7153')
    '''

    if isinstance(data, str):

        # Probing if it is a URL
        if data.startswith('http://') or data.startswith('https://') or data.startswith('ftp://'):
            filename = data.rsplit('/', 1)[-1]

            if schema is None:
                try:
                    schema = metawiki.fn2url(filename)
                except Exception:
                    schema = None

            records = requests.get(data).json()

        # Probing if it is a local path
        elif len(data[:4096]) < 4096 and os.path.exists(data):
            filename = data.rsplit('/', 1)[-1]

            if schema is None:
                try:
                    schema = metawiki.fn2url(filename)
                except Exception:
                    schema = None

            # records = json.load(open(data, 'r'))
            fsource = open(data, 'r')

            if filename.endswith('.yaml') or filename.endswith('.yml'):
                records = yaml.load(fsource)
            else:
                records = json.load(fsource)

        else:
            raise Exception("Unidentified string format. Pass a string, dict, or list")

        if schema:
            return wrap(records, schema)
        else:
            data = records

    if isinstance(data, list):
        ndata = List([Dict(item) for item in data])
        return ndata

    if isinstance(data, dict):
        ndata = Dict(data)
        return ndata


def dump():
    pass


def read_csv(path, schema=None, refresh=False, *args, **kwargs):

    try:
        from pandas import read_csv as p_read_csv
    except Exception:
        print("This command uses pandas, pip install pandas to use it.")

    if schema is None:

        try:

            if path.startswith('http://') or path.startswith('https://') or path.startswith('ftp://'):
                fn = path.rsplit('/', 1)[-1]

            elif len(path[:4096]) < 4096 and os.path.exists(path):
                if '/' in path:
                    fn = fn.rsplit('/', 1)[-1]
                else:
                    fn = path

            schema_url = metawiki.fn2url(fn)
            schema = get_schema(schema_url, refresh=refresh)

        except Exception:
            import pprint
            print("Schema not found. Specify schema, in filename, or as parameter.")
            df_head = p_read_csv(path, *args, **kwargs, nrows=2)
            print("Here is template for convenience.")
            print("schema = ", end="")
            pprint.pprint(template(df_head.head(1).to_dict(orient='records')[0]))
            print("Pass it, like read_csv(path, schema=schema)")

    if schema is not None:
        df = p_read_csv(path, *args, **kwargs)

        df.rename(columns={
            key: (isinstance(schema[key], dict) and schema[key].get('*').rsplit('|', 1)[0]) or
                 (isinstance(schema[key], str) and schema[key].rsplit('|', 1)[0])
            for key in df.columns if key in schema and key != '*'
        }, inplace=True)

        started = False
        for key in schema:
            if key == '*':
                if schema['*'] is not None:
                    df.index.name = schema['*']

            if isinstance(schema[key], dict):
                spec = schema[key].get('*')
            elif isinstance(schema[key], str):
                spec = schema[key]

            if '|' in spec:
                term, rules = spec.rsplit('|')

                if term in df.columns:
                    if not started:
                        print("Converting fields ...")
                        started = True

                    print("%s: %s" % (term, rules))
                    df.loc[:, term] = df[term].apply(lambda x: eval(rules)(x))

        return df


def align(source_list, key_list=None):
    '''
    [Accepts:]
    source_list: list of lists or generators for records
    schema_list: list of schemas of each source
    key_list: list of keys of interest

    [Returns:]
    a single list or generator, that only has fields selected,
    no matter what depth the fields were found in

    >>> metaform.align([[{'a': {'c': 'X'}, 'n': 1}], [{'b': {'a': {'c': 'Y'}}, 'd': {'n': 2}}]], key_list=None)
    '''

    # matching based on shape of first record
    matching = get_match_matrix(
        [source[0] for source in source_list])

    # (the more sources, it might be less shared fields that can be matched)

    # get values by depth and source id
    for i, source in enumerate(source_list):
        for item in source:
            record = {
                key: dictget(item, matching[key][i])
                for key in matching
            }
            yield record
