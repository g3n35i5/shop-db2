from shopdb.api import *
import shopdb.models as models
import shopdb.exceptions as exc
from sqlalchemy.exc import *
from time import sleep
from base import u_emails, u_passwords, u_firstnames, u_lastnames, u_usernames
from base_api import BaseAPITestCase
from flask import json
import jwt
from copy import copy
import pdb


class DeleteUserAPITestCase(BaseAPITestCase):
    def test_delete_user(self):
        """Test for deleting a user"""
        # Create new user which is not verified
        data = {
            'firstname': 'John',
            'lastname': 'Doe',
            'username': 'johnny',
            'email': 'john.doe@test.com',
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
        self.assertException(res, exc.UserCanNotBeDeleted)

    def test_delete_non_existing_user(self):
        """Deleting a user that has been verified should raise an error."""
        res = self.delete(url='/users/5', role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserNotFound)
