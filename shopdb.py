#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import sys

try:
    import configuration as config
except ModuleNotFoundError:
    sys.exit('No configuration file was found. Please make sure, '
             'that you renamed or copied the sample configuration '
             'configuration.example.py and adapted it to your needs.')

import argparse
from shopdb.api import app, db, set_app
from dev import insert_dev_data
from flask_cors import CORS

parser = argparse.ArgumentParser(description='Starting script shop.db')
parser.add_argument('--mode', choices=['development', 'local'])
args = parser.parse_args()

if args.mode == 'development':
    print('Starting shop-db in developing mode')
    set_app(config.DevelopmentConfig)
    app.app_context().push()
    db.create_all()
    insert_dev_data(db)

elif args.mode == 'local':
    print('Starting shop-db on the local database')
    set_app(config.ProductiveConfig)
    CORS(app, expose_headers='*')
    app.app_context().push()

else:
    parser.print_help()
    sys.exit(f'{args.mode}: invalid operating mode')

app.run(host=app.config['HOST'], port=app.config['PORT'])
