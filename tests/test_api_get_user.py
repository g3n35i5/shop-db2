import shopdb.exceptions as exc
from tests.base import u_firstnames, u_lastnames
from tests.base_api import BaseAPITestCase
from flask import json


class GetUserAPITestCase(BaseAPITestCase):
    def test_get_single_user(self):
        """Test for getting a single user"""
        res = self.get(url='/users/1')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'user' in data
        assert 'password' not in data
        self.assertEqual(data['user']['id'], 1)
        self.assertEqual(data['user']['firstname'], u_firstnames[0])
        self.assertEqual(data['user']['lastname'], u_lastnames[0])
        self.assertEqual(data['user']['credit'], 0)
        self.assertTrue(isinstance(data['user']['creation_date'], str))
        self.assertTrue(isinstance(data['user']['verification_date'], str))

    def test_get_non_existing_user(self):
        """Getting a non existing user should raise an error."""
        res = self.get(url='/users/5')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserNotFound)

    def test_get_non_verified_user(self):
        """Getting a non verified user should raise an error."""
        res = self.get(url='/users/4')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsNotVerified)
