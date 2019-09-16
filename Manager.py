#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from shopdb.api import app, set_app, db
import configuration as config

set_app(config.ProductiveConfig)
migrate = Migrate(app, db)
manager = Manager(app)


manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
