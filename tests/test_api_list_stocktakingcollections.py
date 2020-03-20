#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from flask import json

import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase


class ListStocktakingCollectionsAPITestCase(BaseAPITestCase):

    def test_list_stocktaking_collections_as_admin(self):
        """Getting a list of all StocktakingCollections as admin"""
        self.insert_default_stocktakingcollections()
        res = self.get(url='/stocktakingcollections', role='admin')
        self.assertEqual(res.status_code, 200)
        collecttions = json.loads(res.data)
        required = ['id', 'timestamp', 'admin_id', 'revoked']
        for collection in collecttions:
            assert all(x in collection for x in required)

    def test_list_stocktaking_collections_as_user(self):
        """Trying to get a list of all StocktakingCollections as user"""
        res = self.get(url='/stocktakingcollections', role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
