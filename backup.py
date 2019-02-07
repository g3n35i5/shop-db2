#!/usr/bin/env python3

import os
import sys
import errno
import sqlite3
import datetime
from configuration import ProductiveConfig

if __name__ == '__main__':
    _currentDate = datetime.datetime.now()
    _path = ProductiveConfig.BACKUP_DIR + _currentDate.strftime('%Y/%m/%d/')
    _name = 'shop-db_' + _currentDate.strftime('%Y-%m-%d_%H-%M-%S') + '.dump'
    dumpfile = _path + _name

    if not os.path.exists(_path):
        try:
            os.makedirs(os.path.dirname(_path))

        except OSError as exc:
            if exc.errno != errno.EEXIST:
                sys.exit("Error while creating directory.")

    try:
        con = sqlite3.connect(ProductiveConfig.DATABASE_PATH)
    except:
        sys.exit('Could not open shop-db database')

    try:
        f = open(dumpfile, 'w+')

        for line in con.iterdump():
            f.write('{}\n'.format(line))

        f.close()
    except:
        sys.exit('Could not write backup to file "{}"'.format(dumpfile))

    con.close()
