#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
from shopdb.api import db
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class GetUserRefundsAPITestCase(BaseAPITestCase):
    @staticmethod
    def _insert_refunds():
        """Helper function to insert some test refunds."""
        r1 = Refund(user_id=1, total_price=100, admin_id=1, comment='Refund 1')
        r2 = Refund(user_id=2, total_price=200, admin_id=1, comment='Refund 2')
        r3 = Refund(user_id=2, total_price=500, admin_id=1, comment='Refund 3')
        r4 = Refund(user_id=3, total_price=300, admin_id=1, comment='Refund 4')
        r5 = Refund(user_id=2, total_price=2700, admin_id=1, comment='Refund 5')
        for r in [r1, r2, r3, r4, r5]:
            db.session.add(r)
        db.session.commit()

    def test_get_user_refunds(self):
        """This test ensures that all refunds made for a user are listed."""
        self._insert_refunds()
        res = self.get(url='/users/2/refunds')
        self.assertEqual(res.status_code, 200)
        refunds = json.loads(res.data)
        fields = ['id', 'timestamp', 'admin_id', 'total_price', 'revoked',
                  'comment']
        for i in refunds:
            for x in fields:
                assert x in i

    def test_get_user_refunds_no_insert(self):
        """
        This test ensures that an empty list will be returned for a user's
        refunds if none have yet been entered for him.
        """
        res = self.get(url='/users/2/refunds')
        self.assertEqual(res.status_code, 200)
        refunds = json.loads(res.data)
        self.assertEqual(refunds, [])

    def test_get_refunds_non_existing_user(self):
        """
        Getting the refunds from a non existing user should raise an error.
        """
        res = self.get(url='/users/6/refunds')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_get_refunds_non_verified_user(self):
        """
        Getting the refunds from a non verified user should raise an error.
        """
        res = self.get(url='/users/4/refunds')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsNotVerified)

    def test_get_user_refunds_inactive_user(self):
        """
        Getting the refunds from an inactive user should raise an error.
        """
        User.query.filter_by(id=3).first().set_rank_id(4, 1)
        db.session.commit()
        res = self.get(url='/users/3/refunds')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsInactive)
