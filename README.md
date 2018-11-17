# metaform

`pip install --extra-index-url https://pypi.wefindx.io/ metaform`

`$ harvest <resource>`

## Development
Add `~/.pypirc` file:

```
[distutils]
index-servers =
  pypi
  internal

[pypi]
username:<your_pypi_username>
password:<your_pypi_passwd>

[internal]
repository: https://pypi.wefindx.io
username: <wefindx_pypi_username>
password: <wefindx_pypi_passwd>
```

Then, use:
`python setup.py sdist upload internal`
