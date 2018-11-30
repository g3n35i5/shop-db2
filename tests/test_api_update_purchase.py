from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class UpdatePurchaseAPITestCase(BaseAPITestCase):

    def test_update_nothing(self):
        """Updating a purchase with no data should do nothing."""
        self.insert_default_purchases()
        purchase1 = Purchase.query.filter_by(id=1).first()
        res = self.put(url='/purchases/1', data={}, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        purchase2 = Purchase.query.filter_by(id=1).first()
        self.assertEqual(purchase1, purchase2)

    def test_update_forbidden_field(self):
        """Updating a forbidden field should raise an error."""
        self.insert_default_purchases()
        self.assertEqual(Purchase.query.filter_by(id=1).first().id, 1)
        data = {'id': 2}
        res = self.put(url='/purchases/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)
        self.assertEqual(Purchase.query.filter_by(id=1).first().id, 1)

    def test_update_non_existing_purchase(self):
        """Updating a non existing purchase should raise an error."""
        self.insert_default_purchases()
        data = {'amount': 5}
        res = self.put(url='/purchases/6', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.PurchaseNotFound)

    def test_update_revoke_purchase_twice(self):
        """Revoking a purchase twice should raise an error and do nothing."""
        self.insert_default_purchases()
        data = {'revoked': True}
        res = self.put(url='/purchases/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        self.assertTrue(Purchase.query.filter_by(id=1).first().revoked)
        res = self.put(url='/purchases/1', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        self.assertTrue(Purchase.query.filter_by(id=1).first().revoked)

    def test_update_wrong_type(self):
        """A wrong field type should raise an error."""
        self.insert_default_purchases()
        purchase1 = Purchase.query.filter_by(id=1).first()
        data = {'amount': '2'}
        res = self.put(url='/purchases/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        purchase2 = Purchase.query.filter_by(id=1).first()
        self.assertEqual(purchase1, purchase2)

    def test_update_unknown_field(self):
        """An unknown field should raise an error."""
        self.insert_default_purchases()
        data = {'color': 'red'}
        res = self.put(url='/purchases/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_purchase_revoked(self):
        """Update purchase revoked field."""
        self.insert_default_purchases()
        self.assertFalse(Purchase.query.filter_by(id=1).first().revoked)
        data = {'revoked': True}
        res = self.put(url='/purchases/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Updated purchase.')
        self.assertEqual(len(data['updated_fields']), 1)
        self.assertEqual(data['updated_fields'][0], 'revoked')
        self.assertTrue(Purchase.query.filter_by(id=1).first().revoked)

    def test_update_purchase_amount(self):
        """Update product price"""
        self.insert_default_purchases()
        purchase = Purchase.query.filter_by(id=1).first()
        self.assertEqual(purchase.amount, 1)
        self.assertEqual(purchase.price, 300)
        data = {'amount': 10}
        res = self.put(url='/purchases/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Updated purchase.')
        self.assertEqual(len(data['updated_fields']), 1)
        self.assertEqual(data['updated_fields'][0], 'amount')
        purchase = Purchase.query.filter_by(id=1).first()
        self.assertEqual(purchase.amount, 10)
        self.assertEqual(purchase.price, 3000)
