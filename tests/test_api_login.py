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
from copy import copy
import pdb


class LoginAPITestCase(BaseAPITestCase):
    def test_login_user(self):
        '''This test is designed to test the login of an existing user'''
        data = {
            'username': u_usernames[0],
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
