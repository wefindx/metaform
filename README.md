# metaform

`pip install --extra-index-url https://pypi.wefindx.io/ metaform`

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
`python setup.py sdist upload -r internal`

Or also, use:
`pip install -i https://pypi.wefindx.io metadrive`


And then, `requirements.txt` may look like so:
`
metadir==0.0.1
--extra-index-url https://<wefindx_pypi_passwd>@ypi.wefindx.io/<wefindx_pypi_username>/
metaform==0.7.0
`
