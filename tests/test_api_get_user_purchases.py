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


class GetUserPurchasesAPITestCase(BaseAPITestCase):
    def _insert_test_purchases(self):
        """Helper function to insert some test purchases"""
        p1 = Purchase(user_id=1, product_id=1, amount=1)
        p2 = Purchase(user_id=2, product_id=3, amount=2)
        p3 = Purchase(user_id=2, product_id=2, amount=4)
        p4 = Purchase(user_id=3, product_id=1, amount=6)
        p5 = Purchase(user_id=1, product_id=3, amount=8)
        for p in [p1, p2, p3, p4, p5]:
            db.session.add(p)
        db.session.commit()

    def test_get_user_purchases(self):
        """TODO"""
        self._insert_test_purchases()
        res = self.get(url='/users/2/purchases')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'purchases' in data
        fields = ['id', 'timestamp', 'product_id', 'productprice', 'amount',
                  'revoked', 'price']        
        for i in data['purchases']:
            for x in fields:
                assert x in i

    def test_get_users_purchases_no_insert(self):
        """TODO"""
        res = self.get(url='/users/2/purchases')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'purchases' in data
        self.assertEqual(data['purchases'], [])