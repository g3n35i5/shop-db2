# shop-db
This is the documentation for shop.db.

## Table of content

1.  [About shop.db](#about-shopdb)
2.  [Usage](#usage)
3.  [Dependencies](#dependencies)
4.  [Unittests](#unittests)


### About shop.db

We created shop.db in order to offer a simple way to manage purchases and
user interactions in a small community. Over time, the project grew bigger
and bigger and we decided to make it as flexible as possible, so that i can be
used for more applications than our small shop service. Even if the development
of shop.db has not progressed far enough to be called finished, we want to
share the project so anyone can contribute and make shop.db better. In the
following part, you can find a basic documentation for this project.


### Usage

shop.db can be used as a standalone backend and can be accessed via it's API.
Because this is not an elegant way to use this application, we developed the
shop.db frontend, which can be found in it's own repository.


### Dependencies

In order to use shop-db, you need to install the following main dependencies:
  1. Python 3
  2. Python 3 Virtual Environment
  3. pip3
  4. git

```bash
$ sudo apt-get install python3 python3-venv python3-pip  git
```



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
