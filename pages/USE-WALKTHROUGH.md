# Use Walkthrough

**Install and import the package.**

```pip install metaform```

```python
import metaform
```

## Basic Usage

Let's say we have some data:


```python
data = {
    'hello': 1.0,
    'world': 2,
    'how': ['is', {'are': {'you': 'doing'}}]
}
```

We can get the template for defining schema, by `metaform.template`:


```python
metaform.template(data)
```

  {'*': '',
    'hello': {'*': ''},
    'how': [{'*': '', 'are': {'you': {'*': ''}}}],
    'world': {'*': ''}}

This provides an opportunity to specify metadata for each key and the object itself. For example:

```python
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
```

  {'atoms': 2, 'length': 1.0, 'method': ['is', {'yup': {'me': 'doing'}}]}

We recommend saving schemas you create for normalizations for data analytics and [driver projects](https://github.com/drivernet) in dot-folders `.schema`,  in a JSON or YAML files in that folder.

So, we have access to all keys, and can specify, what to do with them:


```python
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
```

  {'atoms': '2ABC',
    'length': 6.0,
    'method': ['is', {'yup': {'me': 'd-o-i-n-g'}}]}


And suppose, we want to define a more complex function, inconvenient via lambdas:

```python
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
```

  {'atoms': '2ABC',
    'length': 222.0,
    'method': ['is', {'yup': {'me': 'd-o-i-n-g'}}]}



We just renamed the keys, and normalized values! What else could we want?

## Normalizing Data

Suppose we have similar data from different sources. For example, topics and comments are not so different after all, because if a comment becomes large enough, it can stand as a topic of its own.


```python
topics = requests.get('https://api.infty.xyz/topics/?format=json').json()['results']
comments = requests.get('https://api.infty.xyz/comments/?format=json').json()['results']
```

Let's define templates for them, with the key names and types to match:


```python
topics_schema = [{
  'id': {'*': 'topic-id'},
  'type': {'*': '|lambda x: {0: "NEED", 1: "GOAL", 2: "IDEA", 3: "PLAN", 4: "STEP", 5: "TASK"}.get(x)'},
  'owner': {'username': {'*': ''}, 'id': {'*': 'user-id'}},
  'blockchain': {'*': '|lambda x: x and True or False'},
}]

normal_topics = metaform.normalize(topics, topics_schema)

topics_df = pandas.io.json.json_normalize(normal_topics)
topics_df.dtypes
```

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

```python
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
```

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

```python
df = pandas.concat([topics_df, comments_df], sort=False)
df.head()
```

<div>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>blockchain</th>
      <th>body</th>
      <th>categories</th>
      <th>categories_names</th>
      <th>children</th>
      <th>comment_count</th>
      <th>created_date</th>
      <th>data</th>
      <th>declared</th>
      <th>editors</th>
      <th>...</th>
      <th>type</th>
      <th>updated_date</th>
      <th>url</th>
      <th>assumed_hours</th>
      <th>claimed_hours</th>
      <th>comment-id</th>
      <th>donated</th>
      <th>parent</th>
      <th>remains</th>
      <th>topic-url</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>0</td>
      <td>True</td>
      <td>.:en\nAdd the **trade.Exchange** model, to ena...</td>
      <td>[]</td>
      <td>[]</td>
      <td>[]</td>
      <td>1.0</td>
      <td>2019-09-21T09:15:48.194279</td>
      <td></td>
      <td>0.15</td>
      <td>[]</td>
      <td>...</td>
      <td>TASK</td>
      <td>2019-09-21T09:34:00.686125</td>
      <td>https://api.infty.xyz/topics/894/?format=json</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
    <tr>
      <td>1</td>
      <td>False</td>
      <td>.:en\nIt would make sense, especially useful i...</td>
      <td>[]</td>
      <td>[]</td>
      <td>[]</td>
      <td>0.0</td>
      <td>2019-09-18T14:15:57.579981</td>
      <td></td>
      <td>0.00</td>
      <td>[]</td>
      <td>...</td>
      <td>TASK</td>
      <td>2019-09-18T14:15:57.580044</td>
      <td>https://api.infty.xyz/topics/893/?format=json</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
    <tr>
      <td>2</td>
      <td>True</td>
      <td>.:lt\nInfinity yra labiau kūrybai skirtas proj...</td>
      <td>[]</td>
      <td>[]</td>
      <td>[]</td>
      <td>0.0</td>
      <td>2019-09-18T11:02:16.678286</td>
      <td></td>
      <td>0.00</td>
      <td>[]</td>
      <td>...</td>
      <td>TASK</td>
      <td>2019-09-18T11:07:45.004434</td>
      <td>https://api.infty.xyz/topics/892/?format=json</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
    <tr>
      <td>3</td>
      <td>True</td>
      <td>.:lt\nKadangi turime įmonių duomenų bazę, tai ...</td>
      <td>[]</td>
      <td>[]</td>
      <td>[https://api.infty.xyz/topics/892/?format=json]</td>
      <td>0.0</td>
      <td>2019-09-18T10:59:47.173797</td>
      <td></td>
      <td>0.00</td>
      <td>[]</td>
      <td>...</td>
      <td>TASK</td>
      <td>2019-09-18T12:48:06.209215</td>
      <td>https://api.infty.xyz/topics/891/?format=json</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
    <tr>
      <td>4</td>
      <td>True</td>
      <td>.:en\nEach goal that we set, is essentially ec...</td>
      <td>[]</td>
      <td>[]</td>
      <td>[]</td>
      <td>1.0</td>
      <td>2019-09-18T01:47:23.604488</td>
      <td></td>
      <td>0.00</td>
      <td>[]</td>
      <td>...</td>
      <td>GOAL</td>
      <td>2019-09-21T10:22:13.226363</td>
      <td>https://api.infty.xyz/topics/890/?format=json</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
    </tr>
  </tbody>
</table>
<p>5 rows × 29 columns</p>
</div>

But that leaves us with a potential alignment problem, if the keys representing the same things appear at different hierarchical places in different sources.

## Aligning Data

So suppose we want to pick out the matching keys at different levels of hierarchies, and put them at the top.

Just for the sake of complexity, let's put the user references deeper somewhere in one of the sources, and remove original:

```python
abnormal_comments = [dict(comment,**{"some": {"place": {"deep": comment["owner"]}}, "owner": None}) for comment in normal_comments]
```

```python
abnormal_comments[0]
```

  {'assumed_hours': '0.00000000',
    'blockchain': True,
    'body': '.:en\n[https://wiki.mindey.com/shared/shots/b51de15b96a58b76fbeb3a1ef.png](https://wiki.mindey.com/shared/shots/b51de15b96a58b76fbeb3a1ef.png)\n{0.15}',
    'claimed_hours': '0.15000000',
    'comment-id': 791,
    'created_date': '2019-09-21T10:05:34.228102',
    'donated': 0.0,
    'languages': ['en'],
    'matched': 0.15,
    'owner': None,
    'parent': None,
    'remains': 0.0,
    'some': {'place': {'deep': {'user-id': 147, 'username': 'Mindey@FE706DAF'}}},
    'topic-url': 'https://api.infty.xyz/topics/894/?format=json',
    'updated_date': '2019-09-21T10:05:54.924341',
    'url': 'https://api.infty.xyz/comments/791/?format=json'}


```python
metaform.align([normal_topics[:1], abnormal_comments[:1]])
```

    <generator object align at 0x7f5207473d58>

```python
list(_)
```

  [{0: 'en',
    'blockchain': True,
    'body': '.:en\nAdd the **trade.Exchange** model, to enable atomic exchange of assets between identities, identities being **users.User**, and assets being things registered as **meta.Instances**, which may be created at the time of operation, if necessary to identify some divisible quantity, like liters of water, or amounts of money .\n\nEach **Exchange** would involve equivalent exchange of hour-money.\n\nSo, an **Exchange** would credit one account, and debit another account.',
    'created_date': '2019-09-21T09:15:48.194279',
    'matched': 0.15,
    'updated_date': '2019-09-21T09:34:00.686125',
    'url': 'https://api.infty.xyz/topics/894/?format=json',
    'user-id': 147,
    'username': 'Mindey@FE706DAF'},
    {0: 'en',
    'blockchain': True,
    'body': '.:en\n[https://wiki.mindey.com/shared/shots/b51de15b96a58b76fbeb3a1ef.png](https://wiki.mindey.com/shared/shots/b51de15b96a58b76fbeb3a1ef.png)\n{0.15}',
    'created_date': '2019-09-21T10:05:34.228102',
    'matched': 0.15,
    'updated_date': '2019-09-21T10:05:54.924341',
    'url': 'https://api.infty.xyz/comments/791/?format=json',
    'user-id': 147,
    'username': 'Mindey@FE706DAF'}]
