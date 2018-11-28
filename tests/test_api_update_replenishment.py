from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class UpdateReplenishmentAPITestCase(BaseAPITestCase):

    def test_update_replenishment_as_admin(self):
        """Updating amount and price of a single replenishment"""
        data = {'amount': 20, 'total_price': 400}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message', 'updated_fields' in data
        self.assertEqual(data['message'], 'Updated replenishment.')
        self.assertEqual(data['updated_fields'], ['amount', 'total_price'])
        repl = Replenishment.query.filter_by(id=1).first()
        self.assertEqual(repl.amount, 20)
        self.assertEqual(repl.total_price, 400)

    def test_update_replenishment_no_changes(self):
        """Updating a single replenishment with same amount and price"""
        data = {'amount': 10, 'total_price': 3000}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_update_replenishment_as_user(self):
        """Updating a single replenishment as user"""
        data = {'amount': 0, 'total_price': 0}
        res = self.put(url='/replenishments/1', data=data, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_update_replenishment_with_invalid_id(self):
        """Updating a single replenishment that does not exist"""
        data = {'amount': 0, 'total_price': 0}
        res = self.put(url='/replenishments/5', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ReplenishmentNotFound)

    def test_update_replenishment_with_forbidden_field(self):
        """Updating a forbidden field of a single replenishment"""
        data = {'amount': 0, 'total_price': 0, 'product_id': 1}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)

    def test_update_replenishment_with_unknown_field(self):
        """Updating a unknown field of a single replenishment"""
        data = {'amount': 0, 'total_price': 0, 'Nonse': '2'}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_replenishment_with_wrong_type(self):
        """Updating a field of a single replenishment with a wrong type"""
        data = {'amount': 0, 'total_price': '1'}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_update_replenishment_with_data_missing(self):
        """Updating a single replenishment with no amount given"""
        data = {'amount': 0}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

