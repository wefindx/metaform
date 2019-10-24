# Using Metaform

**1. Get metaform in Python 3.6+**.

`pip install metaform`

**2. Let's say we have some data, and its generic structure.**

```python
import metaform

data = metaform.requests.get('https://www.metaculus.com/api2/questions/').json()

metaform.template(data)
```
Produces template:
```json
{'count': {'*': ''},
 'results': [{'url': {'*': ''},
   'page_url': {'*': ''},
    ...
   'metaculus_prediction': [{'*': ''}],
   '*': ''}],
 '*': ''}
```

**3. Use the template as a guide to define what part you want to normalize.**

```python
schema = {
    'results': [
        {'prediction_timeseries': [{'t': {'*': 'time|lambda x: int(x)'}}]}
    ]
}
```

**4. APply the schema to get normalized data.**

```python
metaform.normalize(data, schema) # optional: slugify=True -- slugifies keys
```
