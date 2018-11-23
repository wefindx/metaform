import importlib

import os
import re

from boltons.iterutils import remap

from metaform.utils import (
    dictget,
    metapath,
    slug,
    get_match_matrix,
    _add,
    _sub
)

# convenience alias #
from metaform.schema_readers import get_schema #noqa
from metaform.utils import metaplate #noqa
from metaform.utils import metaplate as template #noqa
from metaform.utils import get_concept
from metaform import converters
import metawiki

import pymongo
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

def formatize(ndata, ignore=[], no_convert=[]):
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

    # def __init__(self, *args, **kwargs):
    #     self.update(*args, **kwargs)
    #     if self.get('*'):
    #         print(self.get('*'))

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
        service_name = concept.rsplit('#',1)[-1]
        class_name = concept.rsplit('/',1)[-1].split('#',1)[0].title()

        if '_:emitter' in schema.keys():
            if schema['_:emitter'].startswith('PyPI:metadrive.'):

                # from metadrive.[service_name].[api] import class_name
                api = importlib.import_module(
                    'metadrive.{service_name}.api'.format(
                        service_name=service_name))

                # Map actions to interface.
                Klass = getattr(api, class_name)

                # # from metadrive.[service_name] import login
                if self.get('+'):
                    service = importlib.import_module(
                        'metadrive.{service_name}'.format(
                            service_name=service_name))

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


    def format(self, lang=None, refresh=False):
        if lang:
            return translate(formatize(normalize(self), no_convert=['url']), lang=lang, refresh=refresh)

        return formatize(normalize(self))

    def render(self, lang, refresh=False):
        return translate(normalize(self), lang=lang, refresh=refresh)

class List(list):

    def format(self, lang=None, refresh=False):
        if lang:
            return translate(formatize([normalize(item) for item in self], no_convert=['url']), lang=lang, refresh=refresh)

        return formatize([normalize(item) for item in self])

    def render(self, lang, refresh=False, strip_asterisk=True):
        return translate([normalize(item) for item in self], lang=lang, refresh=refresh)

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
        if data.endswith('.csv'):
            filename = data.rsplit('/',1)[-1]
            import csv
            records = [dict(row) for row in csv.DictReader(open(data))]
            if 'SCANME.md' in os.listdir('.'):
                import yaml
                if not schema:
                    scanme = yaml.load(open('SCANME.md').read().split('```yaml\n',1)[-1].split('\n```',1)[0])
                    schema = get_schema(scanme.get(filename).get('*'))

                if schema:
                    return wrap(records, schema)
                else:
                    # No schema
                    print('No schema found. Specify it in SCANME.md or provide schema parameter.')
                    return records
            else:
                if schema:
                    return wrap(records, schema)
                else:
                    # No schema
                    print('No schema found. Specify it in SCANME.md or provide schema parameter.')
                    return records

    if isinstance(data, pymongo.cursor.Cursor):
        data = list(data)

    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        records = data
    elif data.startswith('http://') or data.startswith('https://'):
        records = requests.get(data).json()
    else:
        records = json.load(open(data))

    if isinstance(records, list):
        ndata = List([Dict(item) for item in records])
    elif isinstance(records, dict):
        ndata = Dict(records)

    return ndata

def read(term, limit=None):
    '''
    calls '_:emitter'

    Reads term as source, where there is '_:emitter' attribute.

    The attribute has to specify one or more functions, that are generators of Dict objects.

    Examples:
    >>> read('::mindey/topic#halfbakery')
    >>> read('https://github.com/mindey/-/wiki/topic#halfbakery')
    '''
    template = get_schema(term)

    readers = template.get('_:emitter')

    if not readers:
        raise Exception('Readers not found in template.')

    if isinstance(readers, list):

        for i, reader in enumerate(readers):
            print(i+1, reader)

        reader_id = input("Choose reader [1] ")

        if not reader_id:
            reader_id = 1
        else:
            reader_id = int(reader_id)

        if reader_id not in range(1, len(readers)+1):
            raise Exception("The choice does not exist.")

        reader_id -= 1
        reader = readers[reader_id]

    elif isinstance(readers, str):
        reader = readers
    else:
        raise Exception("Reader defined as anything other than string or list is not supported.")


    SUPPORTED_PACKAGE_MANAGERS = ['pypi']

    if reader.lower().split(':',1)[0] not in SUPPORTED_PACKAGE_MANAGERS:
        raise Exception(
            "Unknown package manager. " +
            "Make sure the reader you chose starts with one of these: " +
            "{}. Your chosen reader is: {}".format(
                ', '.join(SUPPORTED_PACKAGE_MANAGERS),
                reader
            )
        )

    SUPPORTED_PACKAGES = [
        'pypi:metadrive',
        'pypi:drivers',
        'pypi:subtools'
    ]

    package_name = reader.split('.', 1)[0].lower()

    if package_name not in SUPPORTED_PACKAGES:
        raise Exception(
            "Unsupported reader package. " +
            "Make sure the reader package is one of these: " +
            "{}. Your chosen reader is: {}".format(
                ', '.join(SUPPORTED_PACKAGES),
                package_name
            )

        )

    packman, package = package_name.split(':')

    # Make sure we have that package installed.
    spec = importlib.util.find_spec(package)
    if spec is None:
        answer = input(package +" is not installed. Install it? [y/N] ")
        if answer in ['y', 'Y']:
            try:
                #easy_install.main( ["-U", package_name] )
                os.system('pip install --no-input -U {} --no-cache'.format(package))
            except SystemExit as e:
                pass
        else:
            raise Exception(package_name +" is required. Install it and run again.")
    else:
        # Check the version installed.
        import pkg_resources
        importlib.reload(pkg_resources)
        installed_version = pkg_resources.get_distribution(package).version

        # Check the latest version in PyPI
        from yolk.pypi import CheeseShop

        def get_lastest_version_number(package_name):
            pkg, all_versions = CheeseShop().query_versions_pypi(package_name)
            if len(all_versions):
                return all_versions[0]
            return None

        latest_version = get_lastest_version_number(package)


        def cmp_version(version1, version2):
            def norm(v):
                return [int(x) for x in re.sub(r'(\.0+)*$','', v).split(".")]
            return cmp(norm(version1), norm(version2))

        if latest_version is not None:
            if cmp_version(installed_version,latest_version) < 0:
                answer = input('You are running {}=={}'.format(package,installed_version)+", but there is newer ({}) version. Upgrade it? [y/N] ".format(latest_version))
                if answer in ['y', 'Y']:
                    try:
                        os.system('pip install --no-input -U {} --no-cache'.format(package))
                    except SystemExit as e:
                        pass




    module = __import__(package)

    # Get method and package:
    namespace = reader.split('.', 1)[-1]

    method = module
    for name in namespace.split('.'):
        method = getattr(method, name)

    return method(limit=limit)

def dump():
    pass


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
