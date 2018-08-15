# shop-db
This is the documentation for shop.db.

## Table of content

1.  [Unittests](#unittests)


### Unittests
Currently, most of the core features of shop-db are covered with the
corresponding unittests. In order to execute them you can use the command

```bash
$ python -m coverage run test.py
```

If you want to check the test coverage, type

```bash
$ python -m coverage html
```
to generate the html preview and open a webserver in the newly created
directory `htmlcov`

```bash
$ cd htmlcov
$ python -m http.server
```
