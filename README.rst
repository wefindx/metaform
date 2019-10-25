metaform
========

.. image:: https://badge.fury.io/py/metaform.svg
    :target: https://badge.fury.io/py/metaform
.. image:: https://badges.gitter.im/djrobstep/csvx.svg
   :alt: Join the chat at https://gitter.im/wefindx/metaform
   :target: https://gitter.im/wefindx/metaform

Metaform is a package for hierarchical and nested data normalization.

.. image:: https://wiki.mindey.com/shared/shots/53dcf81b7efd0573f07c5f562.png
   :target: https://wiki.mindey.com/shared/shots/56542f97f99a2b3886baa661f-what-is-metaform.mp4

Basic Usage
-----------

``pip install metaform``

.. code:: python

   import metaform

Let’s say we have some data:

.. code:: python

   data = {
       'hello': 1.0,
       'world': 2,
       'how': ['is', {'are': {'you': 'doing'}}]
   }

We can get the template for defining schema, by ``metaform.template``:

.. code:: python

   metaform.template(data)

::

   {'*': '',
    'hello': {'*': ''},
    'how': [{'*': '', 'are': {'you': {'*': ''}}}],
    'world': {'*': ''}}

This provides an opportunity to specify metadata for each key and the
object itself. For example:

.. code:: python

   schema = {
       '*': 'greeting',
       'hello': {'*': 'length'},
       'world': {'*': 'atoms'},
       'how': [
            {'*': 'method',
             'are': {
                 '*': 'yup',
                 'you': {'*': 'me'}}
            }
       ]}

   metaform.normalize(data, schema)

::

   {'atoms': 2, 'length': 1.0, 'method': ['is', {'yup': {'me': 'doing'}}]}

We recommend saving schemas you create for normalizations for data
analytics and `driver projects <https://github.com/drivernet>`__ in
dot-folders ``.schema``, in a JSON or YAML files in that folder.

So, we have access to all keys, and can specify, what to do with them:

.. code:: python

   schema = {
       '*': 'greeting',
       'hello': {'*': 'length|lambda x: x+5.'},
       'world': {'*': 'atoms|lambda x: str(x)+"ABC"'},
       'how': [
            {'*': 'method',
             'are': {
                 '*': 'yup',
                 'you': {'*': 'me|lambda x: "-".join(list(x))'}}
            }
       ]}

   metaform.normalize(data, schema)

::

   {'atoms': '2ABC',
    'length': 6.0,
    'method': ['is', {'yup': {'me': 'd-o-i-n-g'}}]}

And suppose, we want to define a more complex function, inconvenient via
lambdas:

.. code:: python

   from metaform import converters

   def some_func(x):
       a = 123
       b = 345
       return (b-a)*x

   converters.func = some_func

   schema = {
       '*': 'greeting',
       'hello': {'*': 'length|converters.func'},
       'world': {'*': 'atoms|lambda x: str(x)+"ABC"'},
       'how': [
            {'*': 'method',
             'are': {
                 '*': 'yup',
                 'you': {'*': 'me|lambda x: "-".join(list(x))'}}
            }
       ]}

   metaform.normalize(data, schema)

::

   {'atoms': '2ABC',
    'length': 222.0,
    'method': ['is', {'yup': {'me': 'd-o-i-n-g'}}]}

We just renamed the keys, and normalized values! What else could we
want?

Normalizing Data
----------------

Suppose we have similar data from different sources. For example, topics
and comments are not so different after all, because if a comment
becomes large enough, it can stand as a topic of its own.

.. code:: python

   topics = requests.get('https://api.infty.xyz/topics/?format=json').json()['results']
   comments = requests.get('https://api.infty.xyz/comments/?format=json').json()['results']

Let’s define templates for them, with the key names and types to match:

.. code:: python

   topics_schema = [{
     'id': {'*': 'topic-id'},
     'type': {'*': '|lambda x: {0: "NEED", 1: "GOAL", 2: "IDEA", 3: "PLAN", 4: "STEP", 5: "TASK"}.get(x)'},
     'owner': {'username': {'*': ''}, 'id': {'*': 'user-id'}},
     'blockchain': {'*': '|lambda x: x and True or False'},
   }]

   normal_topics = metaform.normalize(topics, topics_schema)

   topics_df = pandas.io.json.json_normalize(normal_topics)
   topics_df.dtypes

::

   blockchain             bool
   body                 object
   categories           object
   categories_names     object
   children             object
   comment_count         int64
   created_date         object
   data                 object
   declared            float64
   editors              object
   funds               float64
   is_draft               bool
   languages            object
   matched             float64
   owner.user-id         int64
   owner.username       object
   parents              object
   title                object
   topic-id              int64
   type                 object
   updated_date         object
   url                  object
   dtype: object

.. code:: python

   comments_schema = [{
     'id': {'*': 'comment-id'},
     'topic': {'*': 'topic-url'},
     'text': {'*': 'body'},
     'owner': {'username': {'*': ''}, 'id': {'*': 'user-id'}},
     'blockchain': {'*': '|lambda x: x and True or False'},
   }]

   normal_comments = metaform.normalize(comments, comments_schema)

   comments_df = pandas.io.json.json_normalize(normal_comments)
   comments_df.dtypes

::

   assumed_hours      object
   blockchain           bool
   body               object
   claimed_hours      object
   comment-id          int64
   created_date       object
   donated           float64
   languages          object
   matched           float64
   owner.user-id       int64
   owner.username     object
   parent             object
   remains           float64
   topic-url          object
   updated_date       object
   url                object
   dtype: object

.. code:: python

   df = pandas.concat([topics_df, comments_df], sort=False)
