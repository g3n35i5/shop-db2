#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase


class GetStocktakingCollectionAPITestCase(BaseAPITestCase):
    def test_get_stocktakingcollection_as_admin(self):
        """Getting a single stocktakingcollection as admin"""
        self.insert_default_stocktakingcollections()
        res = self.get(url="/stocktakingcollections/1", role="admin")
        self.assertEqual(res.status_code, 200)
        collection = json.loads(res.data)
        required_collection = [
            "id",
            "timestamp",
            "admin_id",
            "stocktakings",
            "revoked",
            "revokehistory",
        ]
        required_stocktaking = ["id", "collection_id", "product_id", "count"]
        assert all(x in collection for x in required_collection)
        stocktakings = collection["stocktakings"]
        for stocktaking in stocktakings:
            assert all(x in stocktaking for x in required_stocktaking)

    def test_get_stocktakingcollection_as_user(self):
        """Trying to get a single stocktakingcollection as user"""
        res = self.get(url="/stocktakingcollections/2", role="user")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_get_non_existing_stocktakingcollection(self):
        """
        This test ensures that an exception is raised if the requested
        stocktakingcollection does not exist.
        """
        self.insert_default_stocktakingcollections()
        res = self.get(url="/stocktakingcollections/5", role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)
