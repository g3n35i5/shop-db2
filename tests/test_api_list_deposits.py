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


class ListDepositsAPITestCase(BaseAPITestCase):
    def insert_test_deposits(self):
        """Helper function to insert some test deposits"""
        d1 = Deposit(user_id=1, amount=100, admin_id=1, comment='Test deposit')
        d2 = Deposit(user_id=2, amount=200, admin_id=1, comment='Test deposit')
        d3 = Deposit(user_id=2, amount=500, admin_id=1, comment='Test deposit')
        d4 = Deposit(user_id=3, amount=300, admin_id=1, comment='Test deposit')
        d5 = Deposit(user_id=1, amount=600, admin_id=1, comment='Test deposit')
        for d in [d1, d2, d3, d4, d5]:
            db.session.add(d)
        db.session.commit()

    def test_list_deposits_as_admin(self):
        """Test for listing all deposits as admin"""
        # Do 5 deposits
        self.insert_test_deposits()
        res = self.get(url='/deposits', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'deposits' in data
        deposits = data['deposits']
        self.assertEqual(len(deposits), 5)
        self.assertEqual(deposits[0]['user_id'], 1)
        self.assertEqual(deposits[1]['user_id'], 2)
        self.assertEqual(deposits[2]['user_id'], 2)
        self.assertEqual(deposits[3]['user_id'], 3)
        self.assertEqual(deposits[4]['user_id'], 1)

        required = ['id', 'timestamp', 'amount', 'comment', 'admin_id',
                    'revoked']
        for deposit in deposits:
            assert all(x in deposit for x in required)

    def test_list_deposits_as_user(self):
        """Test for listing all deposits without token. This should not be
           possible."""
        res = self.get(url='/deposits')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
