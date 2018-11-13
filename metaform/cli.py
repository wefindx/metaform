import click
import json
from metaform import read, slug
from metawiki import name_to_url
import os

# Cause ecryptfs supports max 143 chars.
FILENAME_LENGTH_LIMIT = 143

@click.command()
@click.help_option('-h')
@click.argument('resource', required=True, metavar='<resource>')
@click.option('-l', '--limit', required=False, type=int, help='Limit to the number of records to download.')
@click.option('-o', '--output', required=False, type=str, help='Save results as files to specified folder.')
@click.option('--db', required=False, type=str, help='Save results to specified database.')
def metasync(resource, limit=None, output=None, db=None):
    """Pulls data from a resource, and saves it in data items with metaformat metadata.

    $ metasync <resource>
    """

    if limit:
        limit = int(limit)
    else:
        limit = None

    if not resource.startswith('http'):
        resource = name_to_url(resource)

    for item in read(resource, limit=limit):
        url = item['-']

        print('GET:', url)

        fn = slug(url)[:FILENAME_LENGTH_LIMIT-5]+'.json'

        if output:
            fn = os.path.join(output, fn)

        with open(fn, 'w') as f:
            item['*'] = resource
            f.write(json.dumps(item))

