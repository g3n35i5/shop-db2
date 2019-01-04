from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class UpdatePayoffAPITestCase(BaseAPITestCase):
    def test_update_nothing(self):
        """Updating a payoff with no data should do nothing."""
        self.insert_default_payoffs()
        payoff1 = Payoff.query.filter_by(id=1).first()
        res = self.put(url='/payoffs/1', data={}, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        payoff2 = Payoff.query.filter_by(id=1).first()
        self.assertEqual(payoff1, payoff2)

    def test_update_forbidden_field(self):
        """Updating a forbidden field should raise an error."""
        self.insert_default_payoffs()
        self.assertEqual(Payoff.query.filter_by(id=1).first().id, 1)
        data = {'id': 2}
        res = self.put(url='/payoffs/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)
        self.assertEqual(Payoff.query.filter_by(id=1).first().id, 1)

    def test_update_non_existing_payoff(self):
        """Updating a non existing payoff should raise an error."""
        self.insert_default_payoffs()
        data = {'revoked': True}
        res = self.put(url='/payoffs/6', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_update_revoke_payoff_twice(self):
        """Revoking a payoff twice should raise an error and do nothing."""
        self.insert_default_payoffs()
        data = {'revoked': True}
        res = self.put(url='/payoffs/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        self.assertTrue(Payoff.query.filter_by(id=1).first().revoked)
        res = self.put(url='/payoffs/1', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        self.assertTrue(Payoff.query.filter_by(id=1).first().revoked)

    def test_update_wrong_type(self):
        """A wrong field type should raise an error."""
        self.insert_default_payoffs()
        payoff1 = Payoff.query.filter_by(id=1).first()
        data = {'revoked': "True"}
        res = self.put(url='/payoffs/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        payoff2 = Payoff.query.filter_by(id=1).first()
        self.assertEqual(payoff1, payoff2)

    def test_update_unknown_field(self):
        """An unknown field should raise an error."""
        self.insert_default_payoffs()
        data = {'color': 'red'}
        res = self.put(url='/payoffs/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_payoff_revoked(self):
        """Update payoff revoked field."""
        self.insert_default_payoffs()
        self.assertFalse(Payoff.query.filter_by(id=1).first().revoked)
        data = {'revoked': True}
        res = self.put(url='/payoffs/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Updated payoff.')
        self.assertTrue(Payoff.query.filter_by(id=1).first().revoked)
