from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class DeleteUserAPITestCase(BaseAPITestCase):
    def test_delete_user(self):
        """Test for deleting a user"""
        # Create new user which is not verified
        data = {
            'firstname': 'John',
            'lastname': 'Doe',
            'password': 'supersecret',
            'password_repeat': 'supersecret'
        }
        res = self.post(url='/register', data=data)
        user = User.query.filter_by(id=5).first()
        self.assertFalse(user.is_verified)
        res = self.delete(url='/users/5', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'User deleted.')
        user = User.query.filter_by(id=5).first()
        self.assertEqual(user, None)

    def test_delete_verified_user(self):
        """Deleting a user that has been verified should raise an error."""
        res = self.delete(url='/users/2', role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryCanNotBeDeleted)

    def test_delete_non_existing_user(self):
        """Deleting a user that has been verified should raise an error."""
        res = self.delete(url='/users/5', role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)
