#!/usr/bin/env python3

import sys
import os

try:
    import configuration as config
except ModuleNotFoundError:
    sys.exit('No configuration file was found. Please make sure, '
             'that you renamed or copied the sample configuration '
             'configuration.example.py and adapted it to your needs.')

import argparse
from shopdb.api import *
from dev import insert_dev_data

parser = argparse.ArgumentParser(description='Starting script shop.db')
parser.add_argument('--mode', choices=['development', 'productive'],
                    default='productive')
args = parser.parse_args()

if args.mode == 'development':
    print('Starting shop-db in developing mode')
    set_app(config.DevelopmentConfig)
    app.app_context().push()
    db.create_all()
    insert_dev_data(db)

elif args.mode == 'productive':
    if not os.path.isfile(config.ProductiveConfig.DATABASE_PATH):
        sys.exit('No database found. Please read the documentation and use '
                 'the setupdb.py script to initialize shop-db.')
    print('Starting shop-db in productive mode')
    set_app(config.ProductiveConfig)

else:
    parser.print_help()
    sys.exit(f'{args.mode}: invalid operating mode')

app.run(host=app.config['HOST'], port=app.config['PORT'])
