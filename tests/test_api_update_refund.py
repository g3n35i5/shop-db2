from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class UpdateRefundAPITestCase(BaseAPITestCase):
    def insert_test_refunds(self):
        """Helper function to insert some test refunds"""
        r1 = Refund(user_id=1, total_price=100, admin_id=1,
                    comment='Test refund')
        r2 = Refund(user_id=2, total_price=200, admin_id=1,
                    comment='Test refund')
        r3 = Refund(user_id=2, total_price=500, admin_id=1,
                    comment='Test refund')
        r4 = Refund(user_id=3, total_price=300, admin_id=1,
                    comment='Test refund')
        r5 = Refund(user_id=1, total_price=600, admin_id=1,
                    comment='Test refund')
        for r in [r1, r2, r3, r4, r5]:
            db.session.add(r)
        db.session.commit()

    def test_update_nothing(self):
        """Updating a refund with no data should do nothing."""
        self.insert_test_refunds()
        refund1 = Refund.query.filter_by(id=1).first()
        res = self.put(url='/refunds/1', data={}, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        refund2 = Refund.query.filter_by(id=1).first()
        self.assertEqual(refund1, refund2)

    def test_update_forbidden_field(self):
        """Updating a forbidden field should raise an error."""
        self.insert_test_refunds()
        self.assertEqual(Refund.query.filter_by(id=1).first().id, 1)
        data = {'id': 2}
        res = self.put(url='/refunds/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)
        self.assertEqual(Refund.query.filter_by(id=1).first().id, 1)

    def test_update_non_existing_refund(self):
        """Updating a non existing refund should raise an error."""
        self.insert_test_refunds()
        data = {'revoked': True}
        res = self.put(url='/refunds/6', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.RefundNotFound)

    def test_update_revoke_refund_twice(self):
        """Revoking a refund twice should raise an error and do nothing."""
        self.insert_test_refunds()
        data = {'revoked': True}
        res = self.put(url='/refunds/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        self.assertTrue(Refund.query.filter_by(id=1).first().revoked)
        res = self.put(url='/refunds/1', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        self.assertTrue(Refund.query.filter_by(id=1).first().revoked)

    def test_update_wrong_type(self):
        """A wrong field type should raise an error."""
        self.insert_test_refunds()
        refund1 = Refund.query.filter_by(id=1).first()
        data = {'revoked': "True"}
        res = self.put(url='/refunds/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        refund2 = Refund.query.filter_by(id=1).first()
        self.assertEqual(refund1, refund2)

    def test_update_unknown_field(self):
        """An unknown field should raise an error."""
        self.insert_test_refunds()
        data = {'color': 'red'}
        res = self.put(url='/refunds/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_refund_revoked(self):
        """Update refund revoked field."""
        self.insert_test_refunds()
        self.assertFalse(Refund.query.filter_by(id=1).first().revoked)
        data = {'revoked': True}
        res = self.put(url='/refunds/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Updated refund.')
        self.assertTrue(Refund.query.filter_by(id=1).first().revoked)
