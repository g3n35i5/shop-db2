from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase


class VerifyUserAPITestCase(BaseAPITestCase):
    def test_verify_user(self):
        """Test verifying a user."""
        user = User.query.filter_by(id=4).first()
        self.assertFalse(user.is_verified)
        self.assertFalse(user.verification_date)
        data = {'rank_id': 1}
        res = self.post(url='/verify/4', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        user = User.query.filter_by(id=4).first()
        self.assertTrue(user.is_verified)
        self.assertTrue(isinstance(user.verification_date, datetime.datetime))

    def test_verify_user_twice(self):
        """Test verifying a user twice."""
        user = User.query.filter_by(id=2).first()
        self.assertTrue(user.is_verified)
        data = {'rank_id': 1}
        res = self.post(url='/verify/2', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserAlreadyVerified)

    def test_verify_non_existing_user(self):
        """Test verifying a non existing user."""
        data = {'rank_id': 1}
        res = self.post(url='/verify/5', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserNotFound)

    def test_verify_non_existing_rank(self):
        """Test verifying a user with an invalid rank_id."""
        data = {'rank_id': 5}
        res = self.post(url='/verify/4', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.RankNotFound)
