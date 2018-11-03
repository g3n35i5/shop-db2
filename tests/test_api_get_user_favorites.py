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


class GetUserFavoritesAPITestCase(BaseAPITestCase):
    def _insert_purchases(self):
        """TODO"""
         # Insert user 1 purchases.
        p1 = Purchase(user_id=1, product_id=1, amount=4)
        p2 = Purchase(user_id=1, product_id=2, amount=4)
        p3 = Purchase(user_id=1, product_id=3, amount=5)
        p4 = Purchase(user_id=1, product_id=4, amount=1)
        p5 = Purchase(user_id=1, product_id=3, amount=5)
        p6 = Purchase(user_id=1, product_id=2, amount=4)

        # Insert other users purchases.
        p7 = Purchase(user_id=2, product_id=4, amount=30)
        p8 = Purchase(user_id=3, product_id=3, amount=4)
        p9 = Purchase(user_id=3, product_id=1, amount=12)
        p10 = Purchase(user_id=2, product_id=2, amount=8)
        for p in [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10]:
            db.session.add(p)
        db.session.commit()
        
    def test_get_user_favorites(self):
        """TODO"""
        self._insert_purchases()
        res = self.get(url='/users/1/favorites')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['favorites'], [3, 2, 1, 4])

    def test_get_user_favorites_no_purchase(self):
        """TODO"""
        res = self.get(url='/users/1/favorites')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['favorites'], [])