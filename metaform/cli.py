import click
import json
from metaform import read, slug
from metawiki import name_to_url

@click.command()
@click.help_option('-h')
@click.argument('resource', required=True, metavar='<resource>')
def harvest(resource):
    """Pulls data from a resource, and saves it in data items with metaformat metadata.

    $ harvest <resource>
    """

    if not resource.startswith('http'):
        resource = name_to_url(resource)

    for item in read(resource):
        url = item['-']
        print('GET:', url, end='')

        fn = slug(url)+'.json'

        with open(fn, 'w') as f:
            item['*'] = resource
            f.write(json.dumps(item))
        print(' -> ' + fn)
