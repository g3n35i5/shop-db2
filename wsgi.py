#!/usr/bin/env python3

from __future__ import unicode_literals

import multiprocessing

import gunicorn.app.base

from gunicorn.six import iteritems

import os
import sys
from shopdb.api import app, set_app
import configuration as config


def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1


class StandaloneApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, _app, _options=None):
        self.options = _options or {}
        self.application = _app
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        _config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(_config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


if __name__ == '__main__':
    # Check whether the productive database exists.
    if not os.path.isfile(config.ProductiveConfig.DATABASE_PATH):
        sys.exit('No database found. Please read the documentation and use '
                 'the setupdb.py script to initialize shop-db.')

    # Overwrite the app configuration with the productive settings.
    set_app(config.ProductiveConfig)

    # Set the gunicorn options.
    options = {
        'bind': '%s:%s' % (app.config['HOST'], app.config['PORT']),
        # BEGIN OF WARNING
        # DO NOT CHANGE THIS VALUE, THE APPLICATION IS NOT DESIGNED FOR
        # MULTITHREADING AND ERRORS MAY OCCUR IN THE DATABASE!!!
        'workers': 1
        # END WARNING
    }
    StandaloneApplication(app, options).run()
