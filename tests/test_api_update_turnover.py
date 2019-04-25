from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class UpdateTurnoverAPITestCase(BaseAPITestCase):

    def test_update_nothing(self):
        """Updating a turnover with no data should do nothing."""
        turnover1 = Turnover.query.filter_by(id=1).first()
        res = self.put(url='/turnovers/1', data={}, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        turnover2 = Turnover.query.filter_by(id=1).first()
        self.assertEqual(turnover1, turnover2)

    def test_update_forbidden_field(self):
        """Updating a forbidden field should raise an error."""
        self.assertEqual(Turnover.query.filter_by(id=1).first().id, 1)
        data = {'id': 2}
        res = self.put(url='/turnovers/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)
        self.assertEqual(Turnover.query.filter_by(id=1).first().id, 1)

    def test_update_non_existing_turnover(self):
        """Updating a non existing turnover should raise an error."""
        data = {'revoked': True}
        res = self.put(url='/turnovers/6', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_update_revoke_turnover_twice(self):
        """Revoking a turnover twice should raise an error and do nothing."""
        data = {'revoked': True}
        res = self.put(url='/turnovers/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        self.assertTrue(Turnover.query.filter_by(id=1).first().revoked)
        res = self.put(url='/turnovers/1', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        self.assertTrue(Turnover.query.filter_by(id=1).first().revoked)

    def test_update_wrong_type(self):
        """A wrong field type should raise an error."""
        turnover1 = Turnover.query.filter_by(id=1).first()
        data = {'revoked': 'True'}
        res = self.put(url='/turnovers/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        turnover2 = Turnover.query.filter_by(id=1).first()
        self.assertEqual(turnover1, turnover2)

    def test_update_unknown_field(self):
        """An unknown field should raise an error."""
        data = {'color': 'red'}
        res = self.put(url='/turnovers/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_turnover_revoked(self):
        """Update turnover revoked field."""
        self.assertFalse(Turnover.query.filter_by(id=1).first().revoked)
        data = {'revoked': True}
        res = self.put(url='/turnovers/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Updated turnover.')
        self.assertTrue(Turnover.query.filter_by(id=1).first().revoked)
