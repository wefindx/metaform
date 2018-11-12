import click
import json
from metaform import read, slug
from metawiki import name_to_url
import os

@click.command()
@click.help_option('-h')
@click.argument('resource', required=True, metavar='<resource>')
@click.option('-l', '--limit', required=False, type=int, help='Limit to the number of records to download.')
@click.option('-o', '--output', required=False, type=str, help='Save results as files to specified folder.')
def harvest(resource, limit=None, output=None):
    """Pulls data from a resource, and saves it in data items with metaformat metadata.

    $ harvest <resource>
    """

    if limit:
        limit = int(limit)
    else:
        limit = None

    if not resource.startswith('http'):
        resource = name_to_url(resource)

    for item in read(resource, limit=limit):
        url = item['-']
        print('GET:', url, end='')

        fn = slug(url)+'.json'

        if output:
            fn = os.path.join(output, fn)

        with open(fn, 'w') as f:
            item['*'] = resource
            f.write(json.dumps(item))
        print(' -> ' + fn)
