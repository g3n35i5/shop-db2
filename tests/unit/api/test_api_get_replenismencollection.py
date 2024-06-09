#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase


class GetReplenishmentCollectionAPITestCase(BaseAPITestCase):
    def test_get_replenishmentcollection_as_admin(self):
        """Getting a single replenishmentcollection as admin"""
        self.insert_default_replenishmentcollections()
        res = self.get(url="/replenishmentcollections/1", role="admin")
        self.assertEqual(res.status_code, 200)
        replcoll = json.loads(res.data)
        required_replcoll = [
            "id",
            "timestamp",
            "admin_id",
            "price",
            "comment",
            "replenishments",
            "revoked",
            "revokehistory",
        ]
        required_repl = [
            "id",
            "replcoll_id",
            "product_id",
            "amount",
            "total_price",
            "revoked",
        ]
        assert all(x in replcoll for x in required_replcoll)
        repls = replcoll["replenishments"]
        for repl in repls:
            assert all(x in repl for x in required_repl)

    def test_get_replenishmentcollection_as_user(self):
        """Trying to get a single replenishmentcollection as user"""
        res = self.get(url="/replenishmentcollections/2", role="user")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_get_non_existing_replenishmentcollection(self):
        """This test ensures that an exception is raised if the requested
        replenishmentcollection does not exist.
        """
        self.insert_default_replenishmentcollections()
        res = self.get(url="/replenishmentcollections/5", role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)
