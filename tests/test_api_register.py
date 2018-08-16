#!/usr/bin/env python3

from shopdb.api import *
import shopdb.models as models
import shopdb.exceptions as exc
from sqlalchemy.exc import *
from time import sleep
from base import u_emails, u_passwords, u_firstnames, u_lastnames, u_usernames
from base_api import BaseAPITestCase
from flask import json
import jwt
import pdb


class RegisterAPITestCase(BaseAPITestCase):
    def test_register_user(self):
        '''This test is designed to test the registration of a new user'''
        data = {
            'firstname': 'John',
            'lastname': 'Doe',
            'username': 'johnny',
            'email': 'john.doe@test.com',
            'password': 'supersecret',
            'repeat_password': 'supersecret'
        }
        res = self.post(url='/register', data=data)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Created user.', res.data)

        user = User.query.filter_by(id=5).first()
        self.assertTrue(user)
        self.assertEqual(user.firstname, 'John')
        self.assertEqual(user.lastname, 'Doe')
        self.assertEqual(user.username, 'johnny')
        self.assertEqual(user.email, 'john.doe@test.com')
        self.assertFalse(user.is_verified)

    def test_register_existing_email(self):
        '''This test should ensure that the correct exception gets returned
           on creating a user with an email address already taken.'''
        data = {
            'firstname': 'John',
            'lastname': 'Doe',
            'username': 'johnny',
            'email': u_emails[0],
            'password': 'supersecret',
            'repeat_password': 'supersecret'
        }
        res = self.post(url='/register', data=data)
        self.assertException(res, EmailAddressAlreadyTaken)

        user = User.query.filter_by(id=5).first()
        self.assertFalse(user)

    def test_register_existing_username(self):
        '''This test should ensure that the correct exception gets returned
           on creating a user with an username already taken.'''
        data = {
            'firstname': 'John',
            'lastname': 'Doe',
            'username': u_usernames[0],
            'email': 'john.doe@test.com',
            'password': 'supersecret',
            'repeat_password': 'supersecret'
        }
        res = self.post(url='/register', data=data)
        self.assertException(res, UsernameAlreadyTaken)

        user = User.query.filter_by(id=5).first()
        self.assertFalse(user)
