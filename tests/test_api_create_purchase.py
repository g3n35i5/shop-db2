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


class CreatePurchaseAPITestCase(BaseAPITestCase):
    def test_create_purchase(self):
        """Create a purchase."""
        data = {'user_id': 2, 'product_id': 3, 'amount': 4}
        res = self.post(url='/purchases', data=data)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'Purchase created.')
        purchases = Purchase.query.all()
        self.assertEqual(len(purchases), 1)
        self.assertEqual(purchases[0].user_id, 2)
        self.assertEqual(purchases[0].product_id, 3)
        self.assertEqual(purchases[0].amount, 4)
        self.assertEqual(purchases[0].productprice, 100)
        self.assertEqual(purchases[0].price, 400)
        self.assertFalse(purchases[0].revoked)

    def test_create_purchase_insufficient_credit_alumni(self):
        """Create a purchase with not enough credit."""
        data = {'user_id': 2, 'product_id': 3, 'amount': 21}
        self.assertEqual(User.query.filter_by(id=2).first().rank_id, 3)

        res = self.post(url='/purchases', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InsufficientCredit)

    def test_create_purchase_insufficient_credit_contender(self):
        """Create a purchase with not enough credit."""
        data = {'user_id': 3, 'product_id': 3, 'amount': 4}
        self.assertEqual(User.query.filter_by(id=2).first().rank_id, 3)

        res = self.post(url='/purchases', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InsufficientCredit)

    def test_create_purchase_wrong_type(self):
        """Create a purchase with wrong type(s)."""
        data = {'user_id': 2, 'product_id': 3, 'amount': 4}

        for field in data:
            copy_data = copy(data)
            copy_data[field] = 100.0
            res = self.post(url='/purchases', data=copy_data)
            self.assertEqual(res.status_code, 401)
            self.assertException(res, exc.WrongType)

        self.assertEqual(len(Purchase.query.all()), 0)

    def test_create_purchase_unknown_field(self):
        """Create a purchase with an unknown field."""
        data = {'user_id': 4, 'product_id': 3, 'amount': 4, 'foo': 'bar'}
        res = self.post(url='/purchases', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)
        self.assertEqual(len(Purchase.query.all()), 0)

    def test_create_purchase_not_all_required_fields(self):
        """Create a purchase missing a required field"""
        data = {'user_id': 4, 'product_id': 3}
        res = self.post(url='/purchases', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        self.assertEqual(len(Purchase.query.all()), 0)

    def test_create_purchase_non_verified_user(self):
        """Create a purchase as non verified user."""
        data = {'user_id': 4, 'product_id': 3, 'amount': 4}
        res = self.post(url='/purchases', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsNotVerified)
        self.assertEqual(len(Purchase.query.all()), 0)

    def test_create_purchase_non_existing_user(self):
        """Create a purchase as non existing user."""
        data = {'user_id': 5, 'product_id': 3, 'amount': 4}
        res = self.post(url='/purchases', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserNotFound)
        self.assertEqual(len(Purchase.query.all()), 0)

    def test_create_purchase_inactive_product(self):
        """Create a purchase with an inactive product."""
        product = Product.query.filter_by(id=4).first()
        product.active = False
        db.session.commit()
        data = {'user_id': 1, 'product_id': 4, 'amount': 2}
        res = self.post(url='/purchases', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ProductIsInactive)
        self.assertEqual(len(Purchase.query.all()), 0)

    def test_create_purchase_invalid_amount(self):
        """Create a purchase with an invalid amount."""
        data = {'user_id': 1, 'product_id': 1, 'amount': -1}
        res = self.post(url='/purchases', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidAmount)
        self.assertEqual(len(Purchase.query.all()), 0)

    def test_create_purchase_non_existing_product(self):
        """Create a purchase with a non existing product."""
        data = {'user_id': 1, 'product_id': 5, 'amount': 1}
        res = self.post(url='/purchases', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ProductNotFound)
        self.assertEqual(len(Purchase.query.all()), 0)
