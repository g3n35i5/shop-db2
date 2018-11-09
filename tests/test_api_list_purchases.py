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


class ListPurchasesAPITestCase(BaseAPITestCase):
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

    def test_list_purchases_as_admin(self):
        """Test for listing all purchases as admin"""
        # Do 5 purchases
        self.insert_test_purchases()
        res = self.get(url='/purchases', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'purchases' in data
        purchases = data['purchases']
        self.assertEqual(len(purchases), 5)
        self.assertEqual(purchases[0]['user_id'], 1)
        self.assertEqual(purchases[1]['user_id'], 2)
        self.assertEqual(purchases[2]['user_id'], 2)
        self.assertEqual(purchases[3]['user_id'], 3)
        self.assertEqual(purchases[4]['user_id'], 1)

        required = ['id', 'timestamp', 'user_id', 'product_id', 'productprice',
                    'amount', 'revoked']
        for purchase in purchases:
            assert all(x in purchase for x in required)

    def test_list_purchases_as_user(self):
        """Test for listing all purchases without token. Revoked purchases
           should not be listed."""
        # Do 5 purchases
        self.insert_test_purchases()
        # Revoke the third purchase
        purchase = Purchase.query.filter_by(id=3).first()
        purchase.toggle_revoke(revoked=True)
        db.session.commit()
        res = self.get(url='/purchases')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'purchases' in data
        purchases = data['purchases']
        self.assertEqual(len(purchases), 4)
        self.assertEqual(purchases[0]['user_id'], 1)
        self.assertEqual(purchases[1]['user_id'], 2)
        self.assertEqual(purchases[2]['user_id'], 3)
        self.assertEqual(purchases[3]['user_id'], 1)

        required = ['id', 'timestamp', 'user_id', 'product_id']
        forbidden = ['productprice', 'amount', 'revoked']
        for purchase in purchases:
            assert all(x in purchase for x in required)
            assert all(x not in purchase for x in forbidden)
