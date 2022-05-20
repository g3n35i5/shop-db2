#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase


class GetPurchaseAPITestCase(BaseAPITestCase):
    def test_get_single_purchase(self):
        """Test for getting a single purchase"""
        # Insert test purchases
        self.insert_default_purchases()
        res = self.get(url="/purchases/3")
        self.assertEqual(res.status_code, 200)
        purchase = json.loads(res.data)
        self.assertEqual(purchase["id"], 3)
        self.assertEqual(purchase["user_id"], 2)
        self.assertEqual(purchase["product_id"], 2)
        self.assertEqual(purchase["amount"], 4)
        self.assertEqual(purchase["productprice"], 50)
        self.assertEqual(purchase["price"], 200)
        self.assertFalse(purchase["revoked"])

    def test_get_non_existing_purchase(self):
        """Getting a non existing purchase should raise an error."""
        res = self.get(url="/purchases/5")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)
