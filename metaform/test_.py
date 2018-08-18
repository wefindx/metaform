from metaform import (
    convert,
    normalize,
    metaplate,
    formatize
)

from copy import deepcopy


def test_simple_conversion():

    key = 'something'
    value = '1,234'
    schema = {
        '*': "IN:mindey/thing|lambda _: _.replace(',','')"
    }

    assert convert(key, value, schema) == \
        ('IN:mindey/thing', '1234')

def test_conversion():

    key = 'something'
    value = '1,234'
    schema = {
        '*': "https://www.wikidata.org/wiki/Q82799|lambda _: _.replace(',','')"
    }

    assert convert(key, value, schema) == \
        ('https://www.wikidata.org/wiki/Q82799', '1234')

def test_normalization():

    data = \
    [{'address': {'number': 14, 'street': 'Leonardo str.'},
     'children': [{'age': 1, 'name': 'Mike'}, {'age': 15, 'name': 'Tom'}],
     'name': 'Max'},
    {'address': {'number': 1, 'street': 'Nexus str.'},
     'children': [{'age': 1, 'name': 'Deli'}, {'age': 7, 'name': 'Miki'}],
     'name': 'Dim'}]

    schema = \
    [{'_version': 'domain.com/parents-0.1',
    '*': 'https://www.wikidata.org/wiki/Q7565',
    'address': {'*': 'https://www.wikidata.org/wiki/Q319608',
     'number': {'*': 'https://www.wikidata.org/wiki/Q1413235|lambda _: int(_)'},
     'street': {'*': 'https://www.wikidata.org/wiki/Q24574749'}},
    'children': [{'*': 'https://www.wikidata.org/wiki/Q7569',
      'age': {'*': 'https://www.wikidata.org/wiki/Q185836|lambda _: float(_)'},
      'name': {'*': 'https://www.wikidata.org/wiki/Q82799'}}],
    'name': {'*': 'https://www.wikidata.org/wiki/Q82799'}}]

    result = \
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

    assert normalize(data, schema) == result


def test_make_and_apply_template():

    data = {
        'a': [
            {'b': 'c'},
            {'e': 'f'},
            {'g': 'h'}
        ],
        'b': 'something'
    }

    template = metaplate(data)

    answer = {
        '*': '',
        'a': [
            {'*': '',
             'b': {'*': ''},
             'e': {'*': ''},
             'g': {'*': ''}}
        ],
        'b': {'*': ''}
    }

    assert template == answer

    # apply:

    template['a'][0]['b']['*'] = 'hello'

    result = normalize(data, template)

    answer = deepcopy(data)

    del answer['a'][0]['b']
    answer['a'][0]['hello'] = 'c'

    assert result == answer


def test_make_and_apply_complex_template():
    data = {'fields': {'blockchain': 0,
      'body': '.:en\nThe estimated cost of the laser array is based on extrapolation from the past two decades...',
      'categories': [],
      'comment_count': 37,
      'created_date': '2012-10-14T11:43:11',
      'data': None,
      'editors': [],
      'is_draft': False,
      'languages': '["en"]',
      'owner': 120,
      'parents': [32],
      'source': '',
      'title': '.:en:Cost',
      'type': 5,
      'unsubscribed': [],
      'updated_date': '2017-03-21T11:31:53.338'},
     'model': 'core.topic',
     'pk': 1}

    template = metaplate(data)

    template['fields']['blockchain']['*'] = 'HELLO'

    ndata = normalize(data, template)

    answer = deepcopy(data)
    del answer['fields']['blockchain']
    answer['fields']['hello'] = 0

    assert ndata == answer


import datetime
from urllib.parse import ParseResult

def test_formatization():
    ndata = {
        '_:username#string': 'L2174',
        '_:autobiography#string': {
            '_:body-text#string': '\n\n',
            '_:creation-date#isodate': '2005-04-30T00:00:00',
            '_:last-updated#isodate': '2005-05-01T00:00:00'},
        '_:idea#object': [
            {'_:url#url': 'http://www.na.com/airbag_20active#1118115294',
             '_:title#string': 'airbag active'}]
    }

    expect = {
        '_:username': str('L2174'),
        '_:autobiography': {
            '_:body-text': str('\n\n'),
            '_:creation-date': datetime.datetime(2005, 4, 30, 0, 0),
            '_:last-updated': datetime.datetime(2005, 5, 1, 0, 0)},
        '_:idea': [
            {'_:url': ParseResult(scheme='http', netloc='www.na.com', path='/airbag_20active', params='', query='', fragment='1118115294'),
             '_:title': str('airbag active')}]
    }


    assert formatize(ndata) == expect
