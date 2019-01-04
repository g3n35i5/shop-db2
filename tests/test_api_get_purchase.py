from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class GetPurchaseAPITestCase(BaseAPITestCase):

    def test_get_single_purchase(self):
        """Test for getting a single purchase"""
        # Insert test purchases
        self.insert_default_purchases()
        res = self.get(url='/purchases/3')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'purchase' in data
        purchase = data['purchase']
        self.assertEqual(purchase['id'], 3)
        self.assertEqual(purchase['user_id'], 2)
        self.assertEqual(purchase['product_id'], 2)
        self.assertEqual(purchase['amount'], 4)
        self.assertEqual(purchase['productprice'], 50)
        self.assertEqual(purchase['price'], 200)
        self.assertFalse(purchase['revoked'])

    def test_get_non_existing_purchase(self):
        """Getting a non existing purchase should raise an error."""
        res = self.get(url='/purchases/5')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)
