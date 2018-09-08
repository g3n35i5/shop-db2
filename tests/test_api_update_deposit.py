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


class UpdateDepositAPITestCase(BaseAPITestCase):
    def insert_test_deposits(self):
        '''Helper function to insert some test deposits'''
        d1 = Deposit(user_id=1, amount=100, admin_id=1, comment='Test deposit')
        d2 = Deposit(user_id=2, amount=200, admin_id=1, comment='Test deposit')
        d3 = Deposit(user_id=2, amount=500, admin_id=1, comment='Test deposit')
        d4 = Deposit(user_id=3, amount=300, admin_id=1, comment='Test deposit')
        d5 = Deposit(user_id=1, amount=600, admin_id=1, comment='Test deposit')
        for d in [d1, d2, d3, d4, d5]:
            db.session.add(d)
        db.session.commit()

    def test_update_nothing(self):
        '''Updating a deposit with no data should do nothing.'''
        self.insert_test_deposits()
        deposit1 = Deposit.query.filter_by(id=1).first()
        res = self.put(url='/deposits/1', data={}, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        deposit2 = Deposit.query.filter_by(id=1).first()
        self.assertEqual(deposit1, deposit2)

    def test_update_forbidden_field(self):
        '''Updating a forbidden field should raise an error.'''
        self.insert_test_deposits()
        self.assertEqual(Deposit.query.filter_by(id=1).first().id, 1)
        data = {'id': 2}
        res = self.put(url='/deposits/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)
        self.assertEqual(Deposit.query.filter_by(id=1).first().id, 1)

    def test_update_non_existing_deposit(self):
        '''Updating a non existing deposit should raise an error.'''
        self.insert_test_deposits()
        data = {'amount': 5}
        res = self.put(url='/deposits/6', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DepositNotFound)

    def test_update_revoke_deposit_twice(self):
        '''Revoking a deposit twice should raise an error and do nothing.'''
        self.insert_test_deposits()
        data = {'revoked': True}
        res = self.put(url='/deposits/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        self.assertTrue(Deposit.query.filter_by(id=1).first().revoked)
        res = self.put(url='/deposits/1', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        self.assertTrue(Deposit.query.filter_by(id=1).first().revoked)

    def test_update_wrong_type(self):
        '''A wrong field type should raise an error.'''
        self.insert_test_deposits()
        deposit1 = Deposit.query.filter_by(id=1).first()
        data = {'amount': '2'}
        res = self.put(url='/deposits/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        deposit2 = Deposit.query.filter_by(id=1).first()
        self.assertEqual(deposit1, deposit2)

    def test_update_unknown_field(self):
        '''An unknown field should raise an error.'''
        self.insert_test_deposits()
        data = {'color': 'red'}
        res = self.put(url='/deposits/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_deposit_revoked(self):
        '''Update deposit revoked field.'''
        self.insert_test_deposits()
        self.assertFalse(Deposit.query.filter_by(id=1).first().revoked)
        data = {'revoked': True}
        res = self.put(url='/deposits/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Updated deposit.')
        self.assertEqual(len(data['updated_fields']), 1)
        self.assertEqual(data['updated_fields'][0], 'revoked')
        self.assertTrue(Deposit.query.filter_by(id=1).first().revoked)

    def test_update_deposit_amount(self):
        '''Update product price'''
        self.insert_test_deposits()
        deposit = Deposit.query.filter_by(id=1).first()
        self.assertEqual(deposit.amount, 100)
        data = {'amount': 10}
        res = self.put(url='/deposits/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Updated deposit.')
        self.assertEqual(len(data['updated_fields']), 1)
        self.assertEqual(data['updated_fields'][0], 'amount')
        deposit = Deposit.query.filter_by(id=1).first()
        self.assertEqual(deposit.amount, 10)
