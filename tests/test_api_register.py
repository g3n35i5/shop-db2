#!/usr/bin/env python3

from shopdb.api import *
import shopdb.models as models
import shopdb.exceptions as exc
from sqlalchemy.exc import *
from time import sleep
from base import u_emails, u_passwords
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
