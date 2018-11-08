# Duplicated from pypi:indb
# To remove from other packges, and move it here.

import os
import bs4
import yaml
import slugify
import mistune
import metawiki

from boltons.iterutils import remap
from typology.ontology.infinity import get_source
# from typology.ontology.wikidata import Concept

MAX_HEADER_LEVEL_TO_LOOK = 7

def include_extensions(schema, target, name=''):

    if '_:extends' in schema.keys():
        extends_url = schema['_:extends']

        if not metawiki.isurl(extends_url):
            extends_url = metawiki.name_to_url(extends_url)

        extends = get_schema(extends_url)

        del schema['_:extends']
        if extends:
            if '*' in extends.keys():
                del extends['*']
            if '_clients' in extends.keys():
                del extends['_clients']
            extends.update(schema)
            schema = extends

    clients = available_clients(target.text)

    if clients:
        schema['_clients'] = clients

    schema['*'] = name
    return schema, target


# Replicated in pypi:metaformat.
def get_schema(path):
    '''
    Retrieves all app schemas.

    :path: e.g.,
    https://github.com/mindey/indb/blob/master/apps/kbdmouse.md#key-presses

    '''


    if not os.path.exists(path):
        if not metawiki.isurl(path):
            path = metawiki.name_to_url(path)

    ufn = metawiki.url_to_name(path)

    # Infinity/GitHub case:
    page = get_source(path)

    # Wikidata case:
    # concept =

    anchor = None

    if '#' in path:
        url, anchor = path.rsplit('#', 1)


    soup = bs4.BeautifulSoup(
        mistune.markdown(page),
        'html.parser')


    headers = []

    for header_level in range(1, MAX_HEADER_LEVEL_TO_LOOK):
        headers.extend(soup.find_all('h{}'.format(header_level)))


    if anchor:

        header = None

        for header in headers:
            anchor_slug = slugify.slugify(header.text)

            if anchor_slug == anchor:
                break

        if header:
            content = header.find_next_sibling()

            if content:

                target = content.find(
                    'code', {'class': 'lang-yaml'})

                if target:

                    schema = keys_to_str(yaml.load(target.text))
                    schema = values_to_name(schema)

                    # Expand, if has '_:extends' token.
                    name = path.rsplit('/')[-1]
                    schema, target = include_extensions(schema, target, ufn)

                    return schema

    else:

        schemas = {}

        for header in headers:
            content = header.find_next_sibling()

            target = content.find(
                'code', {'class': 'lang-yaml'})

            if target:
                anchor_slug = slugify.slugify(header.text)

                schema = keys_to_str(yaml.load(target.text))
                schema = values_to_name(schema)

                # Expand, if has '_:extends' token.
                schema, target = include_extensions(schema, target, ufn)

                schemas[anchor_slug] = schema

        return schemas


def available_clients(data):
    splitters = ['clients:', 'clients=']

    for line in data.split('\n'):
        if line[:1] in ['#']:
            for splitter in splitters:
                if splitter in line:
                    return [str(scanner.strip()) for scanner in
                            line.rsplit(splitter,1)[-1].strip().split(',')]
    return []


def keys_to_str(data):

    def visit(path, key, value):
        return str(key), value

    remapped = remap(data, visit=visit)

    return remapped


def values_to_name(data):

    def visit(path, key, value):

        if isinstance(value, str):
            if metawiki.isurl(value):
                value = metawiki.url_to_name(value)

        return key, value

    remapped = remap(data, visit=visit)

    return remapped
