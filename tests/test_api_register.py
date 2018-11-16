from shopdb.api import *
from tests.base_api import BaseAPITestCase
from copy import copy


class RegisterAPITestCase(BaseAPITestCase):
    def test_register_user(self):
        """This test is designed to test the registration of a new user"""
        data = {
            'firstname': 'John',
            'lastname': 'Doe',
            'password': 'supersecret',
            'password_repeat': 'supersecret'
        }
        res = self.post(url='/register', data=data)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Created user.', res.data)

        user = User.query.filter_by(id=5).first()
        self.assertTrue(user)
        self.assertEqual(user.firstname, 'John')
        self.assertEqual(user.lastname, 'Doe')
        self.assertFalse(user.is_verified)

    def test_register_password_too_short(self):
        """This test should ensure that the correct exception gets returned
           on creating a user with a short password."""
        data = {
            'firstname': 'John',
            'lastname': 'Doe',
            'password': 'short',
            'password_repeat': 'short'
        }
        res = self.post(url='/register', data=data)
        self.assertException(res, PasswordTooShort)

        users = User.query.all()
        self.assertEqual(len(users), 4)

    def test_register_missing_data(self):
        """This test should ensure that the correct exception gets returned
           on creating a user with missing data."""
        data = {
            'firstname': 'John',
            'lastname': 'Doe'
        }

        for item in ['firstname', 'lastname']:
            data_copy = copy(data)
            del data_copy[item]
            res = self.post(url='/register', data=data_copy)
            self.assertException(res, DataIsMissing)

        users = User.query.all()
        self.assertEqual(len(users), 4)

    def test_register_wrong_type(self):
        """This test should ensure that the correct exception gets returned
           on creating a user with a wrong data type."""

        data = {
            'firstname': 'John',
            'lastname': 'Doe',
            'password': 'supersecret',
            'password_repeat': 'supersecret'
        }

        for item in ['firstname', 'lastname', 'password', 'password_repeat']:
            data_copy = copy(data)
            data_copy[item] = 1234
            res = self.post(url='/register', data=data_copy)
            self.assertException(res, WrongType)

        users = User.query.all()
        self.assertEqual(len(users), 4)

    def test_register_passwords_do_not_match(self):
        """This test should ensure that the correct exception gets returned
           on creating a user when the passwords do not match."""
        data = {
            'firstname': 'John',
            'lastname': 'Doe',
            'password': 'supersecret',
            'password_repeat': 'supersecret_ooops'
        }
        res = self.post(url='/register', data=data)
        self.assertException(res, PasswordsDoNotMatch)

        users = User.query.all()
        self.assertEqual(len(users), 4)
