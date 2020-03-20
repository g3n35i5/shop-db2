#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from flask import json

import shopdb.exceptions as exc
from shopdb.api import db
from shopdb.models import Deposit, User
from tests.base_api import BaseAPITestCase


class GetUserDepositsAPITestCase(BaseAPITestCase):
    def _insert_deposits(self):
        """Helper function to insert some test deposits."""
        d1 = Deposit(user_id=1, amount=100, admin_id=1, comment='Test deposit')
        d2 = Deposit(user_id=2, amount=200, admin_id=1, comment='Test deposit')
        d3 = Deposit(user_id=2, amount=500, admin_id=1, comment='Test deposit')
        d4 = Deposit(user_id=3, amount=300, admin_id=1, comment='Test deposit')
        d5 = Deposit(user_id=2, amount=2700, admin_id=1, comment='Test deposit')
        for d in [d1, d2, d3, d4, d5]:
            db.session.add(d)
        db.session.commit()

    def test_get_user_deposit(self):
        """This test ensures that all deposits made for a user are listed."""
        self._insert_deposits()
        res = self.get(url='/users/2/deposits')
        self.assertEqual(res.status_code, 200)
        deposits = json.loads(res.data)
        fields = ['id', 'timestamp', 'admin_id', 'amount', 'revoked', 'comment']
        for i in deposits:
            for x in fields:
                assert x in i

    def test_get_user_deposits_no_insert(self):
        """
        This test ensures that an empty list will be returned for a user's
        deposits if none have yet been entered for him.
        """
        res = self.get(url='/users/2/deposits')
        self.assertEqual(res.status_code, 200)
        deposits = json.loads(res.data)
        self.assertEqual(deposits, [])

    def test_get_deposit_non_existing_user(self):
        """
        Getting the deposits from a non existing user should raise an error.
        """
        res = self.get(url='/users/6/deposits')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_get_deposit_non_verified_user(self):
        """
        Getting the deposits from a non verified user should raise an error.
        """
        res = self.get(url='/users/4/deposits')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsNotVerified)

    def test_get_user_deposits_inactive_user(self):
        """
        Getting the deposits from an inactive user should raise an error.
        """
        User.query.filter_by(id=3).first().set_rank_id(4, 1)
        db.session.commit()
        res = self.get(url='/users/3/deposits')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsInactive)
