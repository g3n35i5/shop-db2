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


class LoginAPITestCase(BaseAPITestCase):
    def test_login_user_username(self):
        """This test is designed to test the login of an existing user with
           a username and password"""
        data = {
            'identifier': u_usernames[0],
            'password': u_passwords[0]
        }
        res = self.post(url='/login', data=data)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert all(item in data for item in ['token', 'result'])
        self.assertTrue(data['result'])
        decode = jwt.decode(data['token'], self.app.config['SECRET_KEY'])
        assert 'user' in decode
        self.assertEqual(decode['user']['id'], 1)
        self.assertEqual(decode['user']['firstname'], u_firstnames[0])
        self.assertEqual(decode['user']['lastname'], u_lastnames[0])
        self.assertEqual(decode['user']['username'], u_usernames[0])
        self.assertEqual(decode['user']['email'], u_emails[0])

    def test_login_user_email(self):
        """This test is designed to test the login of an existing user with
           an email address and password"""
        data = {
            'identifier': u_emails[0],
            'password': u_passwords[0]
        }
        res = self.post(url='/login', data=data)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert all(item in data for item in ['token', 'result'])
        self.assertTrue(data['result'])
        decode = jwt.decode(data['token'], self.app.config['SECRET_KEY'])
        assert 'user' in decode
        self.assertEqual(decode['user']['id'], 1)
        self.assertEqual(decode['user']['firstname'], u_firstnames[0])
        self.assertEqual(decode['user']['lastname'], u_lastnames[0])
        self.assertEqual(decode['user']['username'], u_usernames[0])
        self.assertEqual(decode['user']['email'], u_emails[0])

    def test_login_non_verified_user(self):
        """If an authentication attempt is made by a non verified user,
           the correct error message must be returned."""
        # Create a new user.
        data = {
            'firstname': 'John',
            'lastname': 'Doe',
            'username': 'johnny',
            'email': 'john.doe@test.com',
            'password': 'supersecret',
            'password_repeat': 'supersecret'
        }
        res = self.post(url='/register', data=data)

        # Login.
        data = {
            'identifier': 'john.doe@test.com',
            'password': 'supersecret'
        }
        res = self.post(url='/login', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsNotVerified)

    def test_login_missing_password(self):
        """If an authentication attempt is made without a password,
           the correct error message must be returned."""
        data = {
            'identifier': u_emails[0]
        }
        res = self.post(url='/login', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        data = json.loads(res.data)
        assert 'token' not in data

    def test_login_missing_username_and_email(self):
        """If an authentication attempt is made without a username and email
           address, the correct error message must be returned."""
        data = {
            'password': u_passwords[0]
        }
        res = self.post(url='/login', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        data = json.loads(res.data)
        assert 'token' not in data

    def test_login_wrong_email(self):
        """If an authentication attempt is made with a wrong email address,
           the correct error message must be returned."""
        data = {
            'identifier': 'wrong.mail@test.com',
            'password': u_passwords[0]
        }
        res = self.post(url='/login', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidCredentials)
        data = json.loads(res.data)
        assert 'token' not in data

    def test_login_wrong_username(self):
        """If an authentication attempt is made with a wrong username,
           the correct error message must be returned."""
        data = {
            'identifier': 'my_cool_username',
            'password': u_passwords[0]
        }
        res = self.post(url='/login', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidCredentials)
        data = json.loads(res.data)
        assert 'token' not in data

    def test_login_wrong_password(self):
        """If an authentication attempt is made with a password,
           the correct error message must be returned."""
        data = {
            'identifier': u_usernames[0],
            'password': 'my_super_wrong_password'
        }
        res = self.post(url='/login', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidCredentials)
        data = json.loads(res.data)
        assert 'token' not in data
