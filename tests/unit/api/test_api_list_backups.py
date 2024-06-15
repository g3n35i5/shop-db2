#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

import os

from flask import json
from pyfakefs import fake_filesystem_unittest

import shop_db2.exceptions as exc
from tests.base_api import BaseAPITestCase


class TestListBackups(BaseAPITestCase, fake_filesystem_unittest.TestCase):
    def test_authorization(self) -> None:
        """This route should only be available for administrators"""
        res = self.get(url="/backups")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.get(url="/backups", role="user")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_list_backups_no_backups_existing(self) -> None:
        """This test checks whether the return value of the backup route is
        correct when there are no backups.
        """
        res = self.get("/backups", role="admin")
        data = json.loads(res.data)
        self.assertEqual(len(data["backups"]), 0)
        self.assertFalse(data["latest"])

    def test_list_backups(self) -> None:
        """This test checks whether all backups get listed properly."""
        # We are using a fake filesystem to not actually create the files.
        self.setUpPyfakefs()

        # Get the backup directory from the application configuration
        backup_dir = self.app.config["BACKUP_DIR"]

        # Define the fake backup files
        backups = {
            "2019": {
                "01": {
                    "01": [
                        "shop-db_2019-01-01_10-00.dump",
                        "shop-db_2019-01-01_15-00.dump",
                        "shop-db_2019-01-01_20-00.dump",
                    ]
                },
                "02": {
                    "03": [
                        "shop-db_2019-02-03_10-00.dump",
                        "shop-db_2019-02-03_15-00.dump",
                        "shop-db_2019-02-03_20-00.dump",
                    ]
                },
                "03": {"01": ["shop-db_2019-03-01_18-00.dump"]},
            }
        }

        # Create the backup directories in the fake filesystem
        os.makedirs(backup_dir + "/2019/01/01")
        os.makedirs(backup_dir + "/2019/02/03")
        os.makedirs(backup_dir + "/2019/03/01")

        for year in backups.keys():
            for month in backups[year].keys():
                for day in backups[year][month].keys():
                    for file in backups[year][month][day]:
                        _path = "/".join([backup_dir, year, month, day, file])
                        with open(_path, "a"):
                            os.utime(_path, None)

        res = self.get("/backups", role="admin")
        data = json.loads(res.data)
        self.assertEqual(data["backups"], backups)
        self.assertTrue(data["latest"])
