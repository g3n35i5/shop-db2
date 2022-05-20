#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase


class ListReplenishmentCollectionsAPITestCase(BaseAPITestCase):
    def test_list_replenishment_collections_as_admin(self):
        """Getting a list of all ReplenishmentCollections as admin"""
        self.insert_default_replenishmentcollections()
        res = self.get(url="/replenishmentcollections", role="admin")
        self.assertEqual(res.status_code, 200)
        replcolls = json.loads(res.data)
        required = ["id", "timestamp", "admin_id", "price", "revoked", "comment"]
        for replcoll in replcolls:
            assert all(x in replcoll for x in required)

    def test_list_replenishment_collections_as_user(self):
        """Trying to get a list of all ReplenishmentCollections as user"""
        res = self.get(url="/replenishmentcollections", role="user")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
