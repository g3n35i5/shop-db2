# shop-db2
This is the documentation for shop-db.

## Table of content

1.  [About shop.db](#about-shopdb)
2.  [Dependencies](#dependencies)
3.  [Getting started](#getting-started)
4.  [Unittests](#unittests)


### About shop.db

We created shop.db in order to offer a simple way to manage purchases and
user interactions in a small community. Over time, the project grew bigger
and bigger and we decided to make it as flexible as possible, so that i can be
used for more applications than our small shop service. Even if the development
of shop.db has not progressed far enough to be called finished, we want to
share the project so anyone can contribute and make shop.db better. In the
following part, you can find a basic documentation for this project.

shop.db can be used as a standalone backend and can be accessed via it's API.
Because this is not an elegant way to use this application, we developed the
shop.db frontend, which can be found in it's own repository:
[shop-db-frontend](INSERT_LINK "Frontend for shop-db").
Furthermore, the complete administration is carried out via the specially
developed [shop-db-admin](INSERT_LINK "Admin tool for shop-db") interface.

### Dependencies

In order to use shop-db, you need to install the following main dependencies:
  1. Python 3
  2. Python 3 Virtual Environment
  3. pip3
  4. git

```bash
$ sudo apt install python3 python3-venv python3-pip git
```

### Getting started

Add an account for shop-db called shopdb_user. Since this account is only for
running shop-db the extra arguments of -r is added to create a system
account without creating a home directory:

```bash
$ sudo useradd -r shopdb_user
```

Next we will create a directory for the installation of shop-db and change
the owner to the shopdb_user account:

```bash
$ cd /srv
$ sudo git clone <GIT_URL_TO_SHOPDB>
$ sudo chown -R shopdb_user:shopdb_user shop-db2
```

Next up is to create and change to a virtual environment for shop-db. This
will be done as the shopdb_user account:
```bash
$ sudo su -s /bin/bash shopdb_user
$ cd /srv/shop-db2
$ python3 -m venv .
$ source bin/activate
```

Once you have activated the virtual environment you will notice the prompt
change and then you can install the required python modules:

```bash
(shop-db) $ pip3 install -r requirements.txt
```

Now the configuration file of shop-db2 has to be adjusted.
Copy the `configuration.example.py` to the `configuration.py` file:
```bash
(shop-db) $ cp configuration.example.py configuration.py
```

The most important change is the SECRET_KEY. This is later responsible for
salting the user passwords and must be kept secret under all circumstances.
Change this SECRET_KEY in the file `configuration.py`. You can do this with a
normal text editor or with the command `sed`:

```bash
(shop-db) $ sed -i 's/YouWillNeverGuess/YOURBETTERSUPERSECRETKEY/g' configuration.py
```

The first user (and at the same time the first administrator) as well as the
default ranks are created using the `setupdb.py` script. Please look at the
file and check whether the default settings for the ranks meet your
requirements.

If you are satisfied with them, you can now initialize the database:

```bash
(shop-db) $ ./setupdb.py
```

Ready? Almost. To start the Webapi and use the shop-db2 backend, you only have
to start shop-db:

```bash
(shop-db) $ ./shopdb.py
```

However, so that the backend does not have to be started manually every time, it
is advisable to run shop-db as a systemd service:

```bash
(shop-db) $ exit # To switch back to the root user
$ sudo nano /etc/systemd/system/shop-db@shopdb_user.service
```

The file must have the following content:

```
[Unit]
Description=shop-db
After=network-online.target

[Service]
Type=simple
User=%i
ExecStart=/srv/shop-db2/bin/python3 /srv/shop-db2/shopdb.py

[Install]
WantedBy=multi-user.target
```

You need to reload systemd to make the daemon aware of the new configuration:

```bash
$ sudo systemctl --system daemon-reload
```

To have shop-db start automatically at boot, enable the service:

```bash
$ sudo systemctl enable shop-db@shopdb_user
```

To disable the automatic start, use this command:

```bash
$ sudo systemctl disable shop-db@shopdb_user
```

To start shop-db now, use this command:

```bash
$ sudo systemctl start shop-db@shopdb_user
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
to generate the html preview and open a web server in the newly created
directory `htmlcov`

```bash
$ cd htmlcov
$ python -m http.server
```
