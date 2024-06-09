#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

import datetime
import glob
import os
from functools import reduce

from flask import jsonify

from shop_db2.api import app
from shop_db2.helpers.decorators import adminRequired


@app.route("/backups", methods=["GET"])
@adminRequired
def list_backups(admin):
    """Returns a dictionary with all backups in the backup folder.
    The following backup directory structure is assumed for this function:

    [Year]/[Month]/[Day]/shop-db_[Year]-[Month]-[Day]_[Hour]-[Minute].dump

    For example:
    2019/02/07/shop-db_2019-02-07_15-00.dump

    :return: A dictionary containing all backups and the timestamp of the
             latest backup.
    """
    data = {"backups": {}, "latest": None}
    root_dir = app.config["BACKUP_DIR"]
    start = root_dir.rfind(os.sep) + 1
    for path, dirs, files in os.walk(root_dir):
        # Ignore the root path
        if os.path.normpath(path) == os.path.normpath(root_dir):
            continue
        # Ignore all empty folders
        if not dirs and not files:
            continue

        folders = path[start:].split(os.sep)
        subdir = dict.fromkeys(files)

        parent = reduce(dict.get, folders[:-1], data["backups"])

        # We are in the day-directory of our tree
        if len(subdir) != 0:
            parent[folders[-1]] = [key for key in subdir.keys()]
        else:
            parent[folders[-1]] = subdir

    # Get the timestamp of the latest backup
    all_files = glob.glob(root_dir + "**/*.dump", recursive=True)
    if all_files:
        latest = os.path.getctime(max(all_files, key=os.path.getctime))
        data["latest"] = datetime.datetime.fromtimestamp(latest)

    return jsonify(data)
