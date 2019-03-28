from shopdb.api import *
import shopdb.exceptions as exc
from tests.base import BaseTestCase
from copy import copy
import datetime


class RefundModelTestCase(BaseTestCase):

    def test_refund_link_to_its_user(self):
        """
        This test checks whether the reference to the user of a refund is
        working correctly.
        """
        db.session.add(Refund(
            user_id=1,
            total_price=1,
            admin_id=1,
            comment='Foo')
        )
        db.session.commit()
        refund = Refund.query.filter_by(id=1).first()
        self.assertEqual(refund.user, User.query.filter_by(id=1).first())
