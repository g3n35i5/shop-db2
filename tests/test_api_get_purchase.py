from shopdb.api import *
import shopdb.models as models
import shopdb.exceptions as exc
from sqlalchemy.exc import *
from time import sleep
from base import u_emails, u_passwords, u_firstnames, u_lastnames, u_usernames
from base_api import BaseAPITestCase
from flask import json
import jwt
from copy import copy
import pdb


class GetPurchaseAPITestCase(BaseAPITestCase):
    def insert_test_purchases(self):
        """Helper function to insert some test purchases"""
        p1 = Purchase(user_id=1, product_id=1, amount=1)
        p2 = Purchase(user_id=2, product_id=3, amount=2)
        p3 = Purchase(user_id=2, product_id=2, amount=4)
        p4 = Purchase(user_id=3, product_id=1, amount=6)
        p5 = Purchase(user_id=1, product_id=3, amount=8)
        for p in [p1, p2, p3, p4, p5]:
            db.session.add(p)
        db.session.commit()

    def test_get_single_purchase(self):
        """Test for getting a single purchase"""
        # Insert test purchases
        self.insert_test_purchases()
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
        self.assertException(res, exc.PurchaseNotFound)
