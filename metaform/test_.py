from metaform import convert, normalize

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
