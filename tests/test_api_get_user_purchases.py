#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
from shopdb.api import db
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class GetUserPurchasesAPITestCase(BaseAPITestCase):

    def test_get_user_purchases(self):
        """This test ensures that all purchases made by a user are listed."""
        self.insert_default_purchases()
        res = self.get(url='/users/2/purchases')
        self.assertEqual(res.status_code, 200)
        purchases = json.loads(res.data)
        fields = ['id', 'timestamp', 'product_id', 'productprice', 'amount',
                  'revoked', 'price']        
        for i in purchases:
            for x in fields:
                assert x in i

    def test_get_user_purchases_non_existing_user(self):
        """
        This test ensures that an exception is made if the user does not exist.
        """
        self.insert_default_purchases()
        res = self.get(url='/users/6/purchases')
        self.assertException(res, exc.EntryNotFound)

    def test_get_user_purchases_non_verified_user(self):
        """
        This test ensures that an exception is made if the user has not been
        verified yet.
        """
        self.insert_default_purchases()
        res = self.get(url='/users/4/purchases')
        self.assertException(res, exc.UserIsNotVerified)

    def test_get_users_purchases_no_insert(self):
        """
        This test ensures that an empty list is returned for a user's
        purchases if he has not yet made any purchases.
        """
        res = self.get(url='/users/2/purchases')
        self.assertEqual(res.status_code, 200)
        purchases = json.loads(res.data)
        self.assertEqual(purchases, [])

    def test_get_user_purchases_inactive_user(self):
        """
        Getting the purchases from an inactive user should raise an error.
        """
        User.query.filter_by(id=3).first().set_rank_id(4, 1)
        db.session.commit()
        res = self.get(url='/users/3/purchases')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsInactive)
