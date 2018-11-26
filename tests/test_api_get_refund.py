from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class GetRefundsAPITestCase(BaseAPITestCase):
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

    def test_get_refunds_as_admin(self):
        """Test for geting a single refund"""
        # Do 5 refunds
        self.insert_test_refunds()
        res = self.get(url='/refunds/2', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'refund' in data
        refund = data['refund']
        self.assertEqual(refund['id'], 2)
        self.assertEqual(refund['user_id'], 2)
        self.assertEqual(refund['total_price'], 200)
        self.assertFalse(refund['revoked'])

        required = ['id', 'timestamp', 'user_id', 'total_price', 'comment',
                    'revoked', 'revokehistory']
        assert all(x in refund for x in required)
