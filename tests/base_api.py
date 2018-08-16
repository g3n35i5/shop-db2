#!/usr/bin/env python3

from shopdb.api import *
import shopdb.models as models
import shopdb.exceptions as exc
from sqlalchemy.exc import *
from time import sleep
from base import BaseTestCase, u_emails, u_passwords, u_usernames
from flask import json
import jwt
import pdb


class BaseAPITestCase(BaseTestCase):
    def assertException(self, res, exception):
        '''This helper function checks whether the correct exception has
           been raised'''
        data = json.loads(res.data)
        self.assertEqual(res.status_code, exception.code)
        self.assertEqual(data['message'], exception.message)
        self.assertEqual(data['result'], exception.type)

    def _request(self, type, url, data, role):
        '''Helper function to perform a request to the API'''
        if role not in ['admin', 'user', None]:
            sys.exit(f'Wrong role: {role}')

        if role == 'admin':
            email = u_emails[0]
            username = u_usernames[0]
            password = u_passwords[0]
        elif role == 'user':
            email = u_emails[1]
            username = u_usernames[1]
            password = u_passwords[1]
        else:
            email = None
            password = None

        headers = {'content-type': 'application/json'}
        if email and password:
            res = self.login(username, email, password)
            headers['token'] = json.loads(res.data)['token']
        if type == 'POST':
            res = self.client.post(url, data=json.dumps(data), headers=headers)
        elif type == 'PUT':
            res = self.client.put(url, data=json.dumps(data), headers=headers)
        elif type == 'GET':
            res = self.client.get(url, data=json.dumps(data), headers=headers)
        else:
            sys.exit('Wrong request type: {}'.format(_type))

        return res

    def post(self, url, data=None, role=None):
        '''Helper function to perform a POST request to the API'''
        return self._request(type='POST', url=url, data=data, role=role)

    def get(self, url, data=None, role=None):
        '''Helper function to perform a GET request to the API'''
        return self._request(type='GET', url=url, data=data, role=role)

    def put(self, url, data=None, role=None):
        '''Helper function to perform a GET request to the API'''
        return self._request(type='PUT', url=url, data=data, role=role)

    def login(self, username, email, password):
        '''Helper function to perform a login'''
        data = {'email': email, 'password': password, 'username': username}
        return self.client.post('/login', data=json.dumps(data),
                                headers={'content-type': 'application/json'})
