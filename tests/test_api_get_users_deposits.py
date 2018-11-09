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
        data = json.loads(res.data)
        assert 'deposits' in data
        fields = ['id', 'timestamp', 'admin_id', 'amount', 'revoked', 'comment']
        for i in data['deposits']:
            for x in fields:
                assert x in i

    def test_get_user_deposits_no_insert(self):
        """
        This test ensures that an empty list will be returned for a user's deposits
        if none have yet been entered for him.
        """
        res = self.get(url='/users/2/deposits')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'deposits' in data
        self.assertEqual(data['deposits'], [])

    def test_get_deposit_non_existing_user(self):
        """
        Getting the deposits from a non existing user should raise an error.
        """
        res = self.get(url='/users/5/deposits')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserNotFound)

    def test_get_deposit_non_verified_user(self):
        """
        Getting the deposits from a non verified user should raise an error.
        """
        res = self.get(url='/users/4/deposits')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsNotVerified)

        