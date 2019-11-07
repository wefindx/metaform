import datetime
import json
import unittest
from copy import deepcopy

from metaform import Dict, align, convert, converters, formatize, metaplate, normalize, template


class TestMain(unittest.TestCase):

    def setUp(self):
        self.key = 'something'
        self.value = '1,234'

    def test_simple_conversion(self):
        schema = {
            '*': "IN:mindey/thing|lambda _: _.replace(',','')"
        }

        expect = ('IN:mindey/thing', '1234')

        self.assertEqual(convert(self.key, self.value, schema), expect)

    def test_conversion(self):
        schema = {
            '*': "https://www.wikidata.org/wiki/Q82799|lambda _: _.replace(',','')"
        }

        expect = ('https://www.wikidata.org/wiki/Q82799', '1234')

        self.assertEqual(convert(self.key, self.value, schema), expect)

    def test_normalization(self):
        data = [
            {
                'address': {'number': 14, 'street': 'Leonardo str.'},
                'children': [{'age': 1, 'name': 'Mike'}, {'age': 15, 'name': 'Tom'}],
                'name': 'Max'
            },
            {
                'address': {'number': 1, 'street': 'Nexus str.'},
                'children': [{'age': 1, 'name': 'Deli'}, {'age': 7, 'name': 'Miki'}],
                'name': 'Dim'
            }
        ]

        schema = [
            {
                '_version': 'domain.com/parents-0.1',
                '*': 'https://www.wikidata.org/wiki/Q7565',
                'address': {
                    '*': 'https://www.wikidata.org/wiki/Q319608',
                    'number': {'*': 'https://www.wikidata.org/wiki/Q1413235|lambda _: int(_)'},
                    'street': {'*': 'https://www.wikidata.org/wiki/Q24574749'}
                },
                'children': [
                    {
                        '*': 'https://www.wikidata.org/wiki/Q7569',
                        'age': {'*': 'https://www.wikidata.org/wiki/Q185836|lambda _: float(_)'},
                        'name': {'*': 'https://www.wikidata.org/wiki/Q82799'}
                    }
                ],
                'name': {'*': 'https://www.wikidata.org/wiki/Q82799'}
            }
        ]

        result = [
            {
                'WD:Q319608': {
                    'WD:Q1413235': 14,
                    'WD:Q24574749': 'Leonardo str.'
                },
                'WD:Q7569': [
                    {'WD:Q185836': 1.0,
                        'WD:Q82799': 'Mike'},
                    {'WD:Q185836': 15.0,
                        'WD:Q82799': 'Tom'}
                ],
                'WD:Q82799': 'Max'
            },
            {
                'WD:Q319608': {
                    'WD:Q1413235': 1,
                    'WD:Q24574749': 'Nexus str.'
                },
                'WD:Q7569': [
                    {'WD:Q185836': 1.0,
                        'WD:Q82799': 'Deli'},
                    {'WD:Q185836': 7.0,
                        'WD:Q82799': 'Miki'}
                ],
                'WD:Q82799': 'Dim'
            }
        ]

        self.assertEqual(normalize(data, schema, namespace=True), result)

    def test_make_and_apply_template(self):

        data = {
            'a': [
                {'b': 'c'},
                {'e': 'f'},
                {'g': 'h'}
            ],
            'b': 'something'
        }

        tpl = metaplate(data, ret=True)

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

        self.assertEqual(tpl, answer)

        # apply:

        tpl['a'][0]['b']['*'] = 'hello'

        result = normalize(data, tpl)

        answer = deepcopy(data)

        del answer['a'][0]['b']
        answer['a'][0]['hello'] = 'c'

        self.assertEqual(result, answer)

    def test_make_and_apply_complex_template(self):
        data = {
            'fields': {
                'blockchain': 0,
                'body': '.:en\nThe estimated cost of the laser array is based on extrapolation from the past two decades...',  # noqa
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
                'updated_date': '2017-03-21T11:31:53.338'
            },
            'model': 'core.topic',
            'pk': 1
        }

        tpl = metaplate(data, ret=True)

        tpl['fields']['blockchain']['*'] = 'HELLO'

        ndata = normalize(data, tpl, slugify=True)

        answer = deepcopy(data)
        del answer['fields']['blockchain']
        answer['fields']['hello'] = 0

        self.assertEqual(ndata, answer)

    def test_formatization(self):
        ndata = {
            '_:username#string': 'L2174',
            '_:creation-date#unixtime': 1114819200,
            '_:autobiography#string': {
                '_:body-text#string': '\n\n',
                '_:creation-date#isodate': '2005-04-30T00:00:00',
                '_:last-updated#isodate': '2005-05-01T00:00:00'
            },
            '_:idea#object': [
                {'_:url#url': 'http://www.na.com/airbag_20active#1118115294',
                    '_:title#string': 'airbag active'}
            ]
        }

        expect = {
            '_:username': str('L2174'),
            '_:creation-date': datetime.datetime(2005, 4, 30, 0, 0),
            '_:autobiography': {
                '_:body-text': str('\n\n'),
                '_:creation-date': datetime.datetime(2005, 4, 30, 0, 0),
                '_:last-updated': datetime.datetime(2005, 5, 1, 0, 0)},
            '_:idea': [
                {
                    '_:url': 'http://www.na.com/airbag_20active#1118115294',
                    '_:title': str('airbag active')
                }
            ]
        }

        self.assertEqual(formatize(ndata), expect)

    def test_dict_addition_1(self):
        '''
        testing Dict.__add__
        '''
        # It should work for any Dict/List like JSONs.

        a = Dict({'x': 1})
        b = Dict({'x': 1})
        c = Dict({'y': 1})
        d = Dict({'y': [1]})
        e = Dict({'z': {'?': 1}})
        f = Dict({'z': {'?': [1]}})

        assert a + b == {'x': 2}
        assert a + c == {'x': 1, 'y': 1}
        assert a + b + c == {'x': 2, 'y': 1}
        assert d + d == {'y': [1, 1]}
        assert a + d == {'x': 1, 'y': [1]}

        A = Dict({'x': {'y': {'z': 1}, 'u': 2}, 'm': 1, 'n': 2})
        B = Dict({'x': {'y': {'z': 2}, 'u': 8}, 'm': [2], 'n': 3})
        C = Dict({'x': {'y': [{'1': 'Thing A'}, {'2': 'Thing B'}]}})
        D = Dict({'x': {'y': [{'3': 'Thing C'}, {'4': 'Thing D'}]}})

        # Problematic:
        self.assertEqual(c + d, {'y': [1, [1]]})
        # SHOULD BE: {'y': [1,1]}
        self.assertEqual(d + c, {'y': [[1], 1]})
        # SHOULD BE: {'y': [1,1]}
        self.assertEqual(e + f, {'z': [{'?': [1, [1]]}, {'?': [1]}]})
        # SHOULD BE: {'z': {'?': [1,1]]}
        self.assertEqual(A + B,
                         {'x': [{'y': [{'z': 3},
                                       {'z': 2}],
                                 'u': 10},
                                {'y': {'z': 2},
                                 'u': 8}],
                             'm': [1,
                                   [2]],
                             'n': 5})
        # SHOULD BE: {'x': {'y': {'z': 3}, 'u': 10}, 'm': [1,2], 'n': 5}
        self.assertEqual(
            C + D,
            {'x': [{'y': [{'1': 'Thing A', '3': 'Thing C'},
                          {'2': 'Thing B', '4': 'Thing D'},
                          {'3': 'Thing C'},
                          {'4': 'Thing D'}]},
                   {'y': [{'3': 'Thing C'}, {'4': 'Thing D'}]}]}
        )
        # SHOULD BE: {'x': {'y': [{'1': 'Thing A'}, {'2': 'Thing B'}, {'3':
        # 'Thing C'}, {'4': 'Thing D'}]}}

    def test_dict_subtraction_1(self):
        '''
        testing Dict.__sub__
        '''
        a = Dict({'x': 1})
        b = Dict({'x': 1})
        d = Dict({'y': [1]})
        e = Dict({'z': {'?': 1}})
        f = Dict({'z': {'?': [1]}})
        g = Dict({'z': {'?': 1, '!': 1}, 'u': 1})

        empty = {}

        self.assertEqual(b - a, empty)
        self.assertEqual(a - b, empty)
        self.assertEqual(Dict({}) - f, empty)
        self.assertEqual(d - d, {'y': []})

        self.assertEqual(e - e, {'z': {}})

        self.assertEqual(g - e, {'z': {'!': 1}, 'u': 1})

        self.assertEqual(e - f, {'z': {'?': 1}})
        # SHOULD BE: {'z': {'?': []}}


class TestCore(unittest.TestCase):

    def setUp(self):
        self.data = {
            'hello': 1.0,
            'world': 2,
            'how': ['is', {'are': {'you': 'doing'}}]
        }
        with open('metaform/tests/data/topics.json', 'r') as f:
            self.topics = json.load(f)
        with open('metaform/tests/data/comments.json', 'r') as f:
            self.comments = json.load(f)

    def test_generate_template(self):
        expect = {
            '*': '',
            'hello': {'*': ''},
            'how': [{'*': '', 'are': {'you': {'*': ''}}}],
            'world': {'*': ''}
        }
        self.assertEqual(template(self.data), expect)

    def test_rename_keys(self):
        schema = {
            '*': 'greeting',
            'hello': {'*': 'length'},
            'world': {'*': 'atoms'},
            'how': [
                 {
                     '*': 'method',
                     'are': {
                         '*': 'yup',
                         'you': {'*': 'me'}}
                 }
            ]}

        expect = {'atoms': 2,
                  'length': 1.0,
                  'method': ['is', {'yup': {'me': 'doing'}}]}

        self.assertEqual(normalize(self.data, schema), expect)

    def test_apply_lambdas(self):
        schema = {
            '*': 'greeting',
            'hello': {'*': 'length|lambda x: x+5.'},
            'world': {'*': 'atoms|lambda x: str(x)+"ABC"'},
            'how': [
                 {
                     '*': 'method',
                     'are': {
                         '*': 'yup',
                         'you': {'*': 'me|lambda x: "-".join(list(x))'}
                     }
                 }
            ]}

        expect = {
            'atoms': '2ABC',
            'length': 6.0,
            'method': ['is', {'yup': {'me': 'd-o-i-n-g'}}]}

        self.assertEqual(normalize(self.data, schema), expect)

    def test_custom_converters(self):

        def some_func(x):
            a = 123
            b = 345
            return (b - a) * x

        converters.func = some_func

        schema = {
            '*': 'greeting',
            'hello': {'*': 'length|converters.func'},
            'world': {'*': 'atoms|lambda x: str(x)+"ABC"'},
            'how': [
                {
                 '*': 'method',
                 'are': {
                     '*': 'yup',
                     'you': {'*': 'me|lambda x: "-".join(list(x))'}}
                }
            ]}

        expect = {
            'atoms': '2ABC',
            'length': 222.0,
            'method': ['is', {'yup': {'me': 'd-o-i-n-g'}}]}

        self.assertEqual(normalize(self.data, schema), expect)

    def test_merging_topics_and_comments(self):
        topics_schema = [{
            'id': {'*': 'topic-id'},
            'type': {'*': '|lambda x: {0: "NEED", 1: "GOAL", 2: "IDEA", 3: "PLAN", 4: "STEP", 5: "TASK"}.get(x)'},
            'owner': {'username': {'*': ''}, 'id': {'*': 'user-id'}},
            'blockchain': {'*': '|lambda x: x and True or False'},
        }]

        comments_schema = [{
            'id': {'*': 'comment-id'},
            'topic': {'*': 'topic-url'},
            'text': {'*': 'body'},
            'owner': {'username': {'*': ''}, 'id': {'*': 'user-id'}},
            'blockchain': {'*': '|lambda x: x and True or False'},
        }]

        normal_topics = normalize(self.topics, topics_schema)
        normal_comments = normalize(self.comments, comments_schema)

        with open('metaform/tests/data/topics+comments.json', 'r') as f:
            expect = json.load(f)

        self.assertEqual(normal_topics + normal_comments, expect)

    def test_keys_pickout_alignment(self):
        topics_schema = [{
            'id': {'*': 'topic-id'},
            'type': {'*': '|lambda x: {0: "NEED", 1: "GOAL", 2: "IDEA", 3: "PLAN", 4: "STEP", 5: "TASK"}.get(x)'},
            'owner': {'username': {'*': ''}, 'id': {'*': 'user-id'}},
            'blockchain': {'*': '|lambda x: x and True or False'},
        }]
        comments_schema = [{
            'id': {'*': 'comment-id'},
            'topic': {'*': 'topic-url'},
            'text': {'*': 'body'},
            'owner': {'username': {'*': ''}, 'id': {'*': 'user-id'}},
            'blockchain': {'*': '|lambda x: x and True or False'},
        }]

        normal_topics = normalize(self.topics, topics_schema)
        normal_comments = normalize(self.comments, comments_schema)

        abnormal_comments = [
            dict(comment, **{"some": {"place": {"deep": comment["owner"]}}, "owner": None})
            for comment in normal_comments
        ]

        with open('metaform/tests/data/topics+comments-pickout.json', 'r') as f:
            expect = json.load(f)

        self.assertEqual(
            json.loads(json.dumps(list(
                align([normal_topics[:1], abnormal_comments[:1]])
            ))), expect
        )

    def test_keys_renaming(self):
        self.assertEqual(
            normalize({'A': 1}, {'A': {'*': 'B'}}),
            {'B': 1}
        )

    def test_hyphenation(self):
        self.assertEqual(
            normalize({'A': 1}, {'A': {'*': 'a_b'}}),
            {'a_b': 1}
        )

    def test_keys_renaming_slugify(self):
        self.assertEqual(
            normalize({'A': 1}, {'A': {'*': 'B'}}, slugify=True),
            {'b': 1}
        )

    def test_hyphenation_slugify(self):
        self.assertEqual(
            normalize({'A': 1}, {'A': {'*': 'a_b'}}, slugify=True),
            {'a-b': 1}
        )


if __name__ == '__main__':
    unittest.main()
