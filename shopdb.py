#!/usr/bin/env python3

import argparse
import sys
from shopdb.api import *
from dev import insert_dev_data
import configuration as config

parser = argparse.ArgumentParser(description='Starting script shop.db')
parser.add_argument('--mode', choices=['development'])
args = parser.parse_args()

if args.mode == 'development':
    set_app(config.DevelopmentConfig)
    app.app_context().push()
    db.create_all()
    insert_dev_data(db)
else:
    parser.print_help()
    sys.exit(f'{args.mode}: invalid operating mode')

app.run(host=app.config['HOST'], port=app.config['PORT'])
