from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json
from copy import copy


class CreateRefundAPITestCase(BaseAPITestCase):
    def test_create_refund_positive_amount(self):
        """Create a refund with a positive total_price."""
        data = {'user_id': 2, 'total_price': 1000, 'comment': 'Test refund'}
        res = self.post(url='/refunds', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'Created refund.')
        refunds = Refund.query.all()
        self.assertEqual(len(refunds), 1)
        self.assertEqual(refunds[0].user_id, 2)
        self.assertEqual(refunds[0].total_price, 1000)
        self.assertEqual(refunds[0].comment, 'Test refund')
        self.assertFalse(refunds[0].revoked)

    def test_create_refund_invalid_amount(self):
        """Create a refund with an invalid amount."""
        for amount in [-1000, 0]:
            data = {'user_id': 2, 'total_price': amount, 'comment': 'Foo'}
            res = self.post(url='/refunds', data=data, role='admin')
            self.assertEqual(res.status_code, 401)
            self.assertException(res, exc.InvalidAmount)

    def test_create_refund_wrong_type(self):
        """Create a refund with wrong type(s)."""
        data = {'user_id': 2, 'total_price': 1000, 'comment': 'Test refund'}

        for field in data:
            copy_data = copy(data)
            copy_data[field] = 100.0
            res = self.post(url='/refunds', data=copy_data, role='admin')
            self.assertEqual(res.status_code, 401)
            self.assertException(res, exc.WrongType)

        self.assertEqual(len(Refund.query.all()), 0)

    def test_create_refund_unknown_field(self):
        """Create a refund with an unknown field."""
        data = {'user_id': 2, 'total_price': 1000, 'comment': 'Test refund',
                'foo': 'bar'}
        res = self.post(url='/refunds', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)
        self.assertEqual(len(Refund.query.all()), 0)

    def test_create_refund_not_all_required_fields(self):
        """Create a refund with a missing field should raise an error"""
        data = {'user_id': 2, 'total_price': 1000}
        res = self.post(url='/refunds', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        self.assertEqual(len(Refund.query.all()), 0)

    def test_create_refund_non_verified_user(self):
        """Create a refund as non verified user."""
        data = {'user_id': 4, 'total_price': 1000, 'comment': 'Test refund'}
        res = self.post(url='/refunds', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsNotVerified)
        self.assertEqual(len(Refund.query.all()), 0)

    def test_create_refund_non_existing_user(self):
        """Create a refund as non existing user."""
        data = {'user_id': 5, 'total_price': 1000, 'comment': 'Test refund'}
        res = self.post(url='/refunds', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserNotFound)
        self.assertEqual(len(Refund.query.all()), 0)

    def test_create_refund_invalid_amount(self):
        """Create a purchase with an invalid total_price."""
        data = {'user_id': 2, 'total_price': 0, 'comment': 'Test refund'}
        res = self.post(url='/refunds', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidAmount)
        self.assertEqual(len(Refund.query.all()), 0)
