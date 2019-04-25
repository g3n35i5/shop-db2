from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json
from copy import copy


class CreateTurnoverAPITestCase(BaseAPITestCase):
    def test_create_turnover(self):
        """Create a turnover"""
        data = {'amount': 1000, 'comment': 'Test turnover'}
        res = self.post(url='/turnovers', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'Created turnover.')
        turnovers = Turnover.query.all()
        self.assertEqual(len(turnovers), 5)
        self.assertEqual(turnovers[4].amount, 1000)
        self.assertEqual(turnovers[4].admin_id, 1)
        self.assertEqual(turnovers[4].comment, 'Test turnover')
        self.assertFalse(turnovers[4].revoked)

    def test_create_turnover_invalid_amount(self):
        """Create a turnover with an invalid amount."""
        data = {'amount': 0, 'comment': 'Invalid turnover'}
        res = self.post(url='/turnovers', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidAmount)

    def test_create_turnover_wrong_type(self):
        """Create a turnover with wrong type(s)."""
        data = {'amount': 1000, 'comment': 'Test turnover'}

        for field in data:
            copy_data = copy(data)
            copy_data[field] = 100.0
            res = self.post(url='/turnovers', data=copy_data, role='admin')
            self.assertEqual(res.status_code, 401)
            self.assertException(res, exc.WrongType)

        self.assertEqual(len(Turnover.query.all()), 4)

    def test_create_turnover_unknown_field(self):
        """Create a turnover with an unknown field."""
        data = {'amount': 1000, 'comment': 'Test turnover', 'foo': 'bar'}
        res = self.post(url='/turnovers', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)
        self.assertEqual(len(Turnover.query.all()), 4)

    def test_create_turnover_not_all_required_fields(self):
        """Create a turnover with a missing field should raise an error"""
        data = {'amount': 1000}
        res = self.post(url='/turnovers', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        self.assertEqual(len(Turnover.query.all()), 4)