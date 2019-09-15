#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
from shopdb.api import db
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json
from copy import copy


class CreateBatchDepositAPITestCase(BaseAPITestCase):

    def test_create_batch_deposit_positive_amount(self):
        """Create a batch deposit with a positive amount."""
        data = {'user_ids': [1, 2, 3], 'amount': 10, 'comment': 'Batch'}
        res = self.post(url='/deposits/batch', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'Created batch deposit.')
        deposits = Deposit.query.all()
        self.assertEqual(len(deposits), 3)
        for i in [1, 2, 3]:
            self.assertEqual(deposits[i - 1].user_id, i)
            self.assertEqual(deposits[i - 1].amount, 10)
            self.assertEqual(deposits[i - 1].comment, 'Batch')
            self.assertFalse(deposits[i - 1].revoked)

    def test_create_batch_deposit_negative_amount(self):
        """Create a batch deposit with a negative amount."""
        data = {'user_ids': [1, 2, 3], 'amount': -10, 'comment': 'Batch'}
        res = self.post(url='/deposits/batch', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'Created batch deposit.')
        deposits = Deposit.query.all()
        self.assertEqual(len(deposits), 3)
        for i in [1, 2, 3]:
            self.assertEqual(deposits[i - 1].user_id, i)
            self.assertEqual(deposits[i - 1].amount, -10)
            self.assertEqual(deposits[i - 1].comment, 'Batch')
            self.assertFalse(deposits[i - 1].revoked)

    def test_create_batch_deposit_wrong_type(self):
        """Create a deposit with wrong type(s)."""
        data = {'user_ids': [1, 2], 'amount': 1000, 'comment': 'Batch deposit'}

        for field in data:
            copy_data = copy(data)
            copy_data[field] = 100.0
            res = self.post(url='/deposits/batch', data=copy_data, role='admin')
            self.assertEqual(res.status_code, 401)
            self.assertException(res, exc.WrongType)

        self.assertEqual(len(Deposit.query.all()), 0)

    def test_create_batch_deposit_unknown_field(self):
        """Create a batch deposit with an unknown field."""
        data = {'user_ids': [1, 2], 'amount': 1000, 'comment': 'Test deposit',
                'foo': 'bar'}
        res = self.post(url='/deposits/batch', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)
        self.assertEqual(len(Deposit.query.all()), 0)

    def test_create_batch_deposit_not_all_required_fields(self):
        """Create a batch deposit with a missing field should raise an error"""
        data = {'user_ids': [1, 2], 'amount': 1000}
        res = self.post(url='/deposits/batch', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        self.assertEqual(len(Deposit.query.all()), 0)

    def test_create_batch_deposit_non_verified_user(self):
        """Create a batch deposit as non verified user."""
        data = {'user_ids': [3, 4], 'amount': 1000, 'comment': 'Batch deposit'}
        res = self.post(url='/deposits/batch', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsNotVerified)
        self.assertEqual(len(Deposit.query.all()), 0)

    def test_create_batch_deposit_inactive_user(self):
        """Create a deposit for an inactive user."""
        User.query.filter_by(id=3).first().set_rank_id(4, 1)
        db.session.commit()
        data = {'user_ids': [3, 4], 'amount': 1000, 'comment': 'Batch deposit'}
        res = self.post(url='/deposits/batch', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsInactive)
        self.assertEqual(len(Deposit.query.all()), 0)

    def test_create_batch_deposit_non_existing_user(self):
        """Create a batch deposit as non existing user."""
        data = {'user_ids': [3, 5], 'amount': 1000, 'comment': 'Batch deposit'}
        res = self.post(url='/deposits/batch', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)
        self.assertEqual(len(Deposit.query.all()), 0)

    def test_create_batch_deposit_invalid_amount(self):
        """Create a batch deposit with an invalid amount."""
        data = {'user_ids': [1, 2], 'amount': 0, 'comment': 'Batch deposit'}
        res = self.post(url='/deposits/batch', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidAmount)
        self.assertEqual(len(Deposit.query.all()), 0)
