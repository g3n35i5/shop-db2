#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
from shopdb.api import db
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class ListPurchasesAPITestCase(BaseAPITestCase):

    def test_list_purchases_as_admin(self):
        """Test for listing all purchases as admin"""
        # Do 5 purchases
        self.insert_default_purchases()
        res = self.get(url='/purchases', role='admin')
        self.assertEqual(res.status_code, 200)
        purchases = json.loads(res.data)
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
        self.insert_default_purchases()
        # Revoke the third purchase
        purchase = Purchase.query.filter_by(id=3).first()
        purchase.toggle_revoke(revoked=True)
        db.session.commit()
        res = self.get(url='/purchases')
        self.assertEqual(res.status_code, 200)
        purchases = json.loads(res.data)
        self.assertEqual(len(purchases), 4)
        self.assertEqual(purchases[0]['user_id'], 1)
        self.assertEqual(purchases[1]['user_id'], 2)
        self.assertEqual(purchases[2]['user_id'], 3)
        self.assertEqual(purchases[3]['user_id'], 1)

        required = ['id', 'timestamp', 'user_id', 'product_id', 'amount']
        forbidden = ['productprice', 'revoked']
        for purchase in purchases:
            assert all(x in purchase for x in required)
            assert all(x not in purchase for x in forbidden)

    def test_list_purchases_with_limit(self):
        """
        Listing the purchases with a limit.
        """
        # Do 5 purchases
        self.insert_default_purchases()

        # Revoke the third purchase
        purchase = Purchase.query.filter_by(id=3).first()
        purchase.toggle_revoke(revoked=True)
        db.session.commit()

        res = self.get(url='/purchases', params={'limit': 3})
        self.assertEqual(res.status_code, 200)
        purchases = json.loads(res.data)
        self.assertEqual(len(purchases), 3)
        self.assertEqual(purchases[0]['id'], 5)
        self.assertEqual(purchases[1]['id'], 4)  # <- Third purchase is revoked!
        self.assertEqual(purchases[2]['id'], 2)

    def test_invalid_parameter(self):
        res = self.get(url='/purchases', params={'unknown': 2})
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_wrong_parameter_type(self):
        res = self.get(url='/purchases', params={'limit': 'two'})
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
