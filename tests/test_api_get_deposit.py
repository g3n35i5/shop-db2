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


class GetDepositAPITestCase(BaseAPITestCase):
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

    def test_get_single_deposit(self):
        """Test for getting a single deposit"""
        # Insert test deposits
        self.insert_test_deposits()
        res = self.get(url='/deposits/3')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'deposit' in data
        deposit = data['deposit']
        self.assertEqual(deposit['id'], 3)
        self.assertEqual(deposit['user_id'], 2)
        self.assertEqual(deposit['amount'], 500)
        self.assertFalse(deposit['revoked'])

    def test_get_non_existing_deposit(self):
        """Getting a non existing deposit should raise an error."""
        res = self.get(url='/deposits/6')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DepositNotFound)

    def test_get_deposit_revokehistory(self):
        """Getting the revokehistory of a single deposit"""
        self.insert_test_deposits()
        deprevoke = DepositRevoke(deposit_id=1, admin_id=1, revoked=True)
        db.session.add(deprevoke)
        deprevoke = DepositRevoke(deposit_id=1, admin_id=1, revoked=False)
        db.session.add(deprevoke)
        deprevoke = DepositRevoke(deposit_id=1, admin_id=1, revoked=True)
        db.session.add(deprevoke)

        res = self.get(url='/deposits/1')
        data = json.loads(res.data)
        deposit = data['deposit']
        assert 'revokehistory' in deposit
        self.assertEqual(len(deposit['revokehistory']), 3)
        self.assertTrue(deposit['revokehistory'][0]['revoked'])
        self.assertFalse(deposit['revokehistory'][1]['revoked'])
        self.assertTrue(deposit['revokehistory'][2]['revoked'])
