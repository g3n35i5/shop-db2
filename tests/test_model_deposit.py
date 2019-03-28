from shopdb.api import *
import shopdb.exceptions as exc
from tests.base import BaseTestCase
from copy import copy
import datetime


class DepositModelTestCase(BaseTestCase):

    def test_deposit_link_to_its_user(self):
        """
        This test checks whether the reference to the user of a deposit is
        working correctly.
        """
        db.session.add(Deposit(user_id=1, amount=1, admin_id=1, comment='Foo'))
        db.session.commit()
        deposit = Deposit.query.filter_by(id=1).first()
        self.assertEqual(deposit.user, User.query.filter_by(id=1).first())
