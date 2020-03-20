#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
from shopdb.api import db
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json
from copy import copy


class CreateDepositAPITestCase(BaseAPITestCase):
    def test_create_deposit_positive_amount(self):
        """Create a deposit with a positive amount."""
        data = {'user_id': 2, 'amount': 1000, 'comment': 'Test deposit'}
        res = self.post(url='/deposits', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue('message' in data)
        self.assertEqual(data['message'], 'Created deposit.')
        deposits = Deposit.query.all()
        self.assertEqual(len(deposits), 1)
        self.assertEqual(deposits[0].user_id, 2)
        self.assertEqual(deposits[0].amount, 1000)
        self.assertEqual(deposits[0].comment, 'Test deposit')
        self.assertFalse(deposits[0].revoked)

    def test_create_deposit_negative_amount(self):
        """Create a deposit with a negative amount."""
        data = {'user_id': 2, 'amount': -1000, 'comment': 'Test deposit'}
        res = self.post(url='/deposits', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue('message' in data)
        self.assertEqual(data['message'], 'Created deposit.')
        deposits = Deposit.query.all()
        self.assertEqual(len(deposits), 1)
        self.assertEqual(deposits[0].user_id, 2)
        self.assertEqual(deposits[0].amount, -1000)
        self.assertEqual(deposits[0].comment, 'Test deposit')
        self.assertFalse(deposits[0].revoked)

    def test_create_deposit_wrong_type(self):
        """Create a deposit with wrong type(s)."""
        data = {'user_id': 2, 'amount': 1000, 'comment': 'Test deposit'}

        for field in data:
            copy_data = copy(data)
            copy_data[field] = 100.0
            res = self.post(url='/deposits', data=copy_data, role='admin')
            self.assertEqual(res.status_code, 401)
            self.assertException(res, exc.WrongType)

        self.assertEqual(len(Deposit.query.all()), 0)

    def test_create_deposit_unknown_field(self):
        """Create a deposit with an unknown field."""
        data = {'user_id': 2, 'amount': 1000, 'comment': 'Test deposit',
                'foo': 'bar'}
        res = self.post(url='/deposits', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)
        self.assertEqual(len(Deposit.query.all()), 0)

    def test_create_deposit_not_all_required_fields(self):
        """Create a deposit with a missing field should raise an error"""
        data = {'user_id': 2, 'amount': 1000}
        res = self.post(url='/deposits', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        self.assertEqual(len(Deposit.query.all()), 0)

    def test_create_deposit_non_verified_user(self):
        """Create a deposit as non verified user."""
        data = {'user_id': 4, 'amount': 1000, 'comment': 'Test deposit'}
        res = self.post(url='/deposits', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsNotVerified)
        self.assertEqual(len(Deposit.query.all()), 0)

    def test_create_deposit_inactive_user(self):
        """Create a deposit for an inactive user."""
        User.query.filter_by(id=3).first().set_rank_id(4, 1)
        db.session.commit()
        data = {'user_id': 3, 'amount': 1000, 'comment': 'Test deposit'}
        res = self.post(url='/deposits', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsInactive)
        self.assertEqual(len(Deposit.query.all()), 0)

    def test_create_deposit_non_existing_user(self):
        """Create a deposit as non existing user."""
        data = {'user_id': 6, 'amount': 1000, 'comment': 'Test deposit'}
        res = self.post(url='/deposits', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)
        self.assertEqual(len(Deposit.query.all()), 0)

    def test_create_deposit_invalid_amount(self):
        """Create a purchase with an invalid amount."""
        data = {'user_id': 2, 'amount': 0, 'comment': 'Test deposit'}
        res = self.post(url='/deposits', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidAmount)
        self.assertEqual(len(Deposit.query.all()), 0)
