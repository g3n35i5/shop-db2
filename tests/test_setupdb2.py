#!/usr/bin/env python3

import os
from setupdb import create_database
from shopdb.api import *
from shopdb.models import *
from flask_testing import TestCase
import configuration as config
from flask import json
import sys


class TestSetup(TestCase):
    def create_app(self):
        app.config.from_object(config.UnittestConfig)
        return app

    def setUp(self):
        # Create test client
        self.client = app.test_client()


    def _request(self, type, url, data, role, content_type):
        """Helper function to perform a request to the API"""
        if role not in ['admin', 'user', None]:  # pragma: no cover
            sys.exit(f'Wrong role: {role}')

        if role == 'admin':
            id = 1
            password = u_passwords[0]
        elif role == 'user':
            id = 2
            password = u_passwords[1]
        else:
            id = None
            password = None

        # Only serialize the data to JSON if it is a json object.
        if content_type == 'application/json':
            data = json.dumps(data)

        headers = {'content-type': content_type}
        if id and password:
            res = self.login(id, password)
            headers['token'] = json.loads(res.data)['token']
        if type == 'POST':
            res = self.client.post(url, data=data, headers=headers)
        elif type == 'PUT':
            res = self.client.put(url, data=data, headers=headers)
        elif type == 'GET':
            res = self.client.get(url, data=data, headers=headers)
        elif type == 'DELETE':
            res = self.client.delete(url, data=data, headers=headers)
        else:  # pragma: no cover
            sys.exit('Wrong request type: {}'.format(type))

        return res

    def post(self, url, data=None, role=None,
             content_type='application/json'):
        """Helper function to perform a POST request to the API"""
        return self._request(type='POST', url=url, data=data, role=role,
                             content_type=content_type)

    def get(self, url, data=None, role=None,
            content_type='application/json'):
        """Helper function to perform a GET request to the API"""
        return self._request(type='GET', url=url, data=data, role=role,
                             content_type=content_type)

    def put(self, url, data=None, role=None,
            content_type='application/json'):
        """Helper function to perform a GET request to the API"""
        return self._request(type='PUT', url=url, data=data, role=role,
                             content_type=content_type)

    def delete(self, url, data=None, role=None,
               content_type='application/json'):
        """Helper function to perform a DELETE request to the API"""
        return self._request(type='DELETE', url=url, data=data, role=role,
                             content_type=content_type)

    def login(self, id, password):
        """Helper function to perform a login"""
        data = {'id': id, 'password': password}
        return self.client.post('/login', data=json.dumps(data),
                                headers={'content-type': 'application/json'})

    def test_setup(self):
        database = os.path.isfile(config.ProductiveConfig.DATABASE_PATH)
        if not database:
            create_database()
        else:
            os.remove(config.ProductiveConfig.DATABASE_PATH)
            create_database()
        res = self.get(url='/users')
        pdb.set_trace()
        os.remove(config.ProductiveConfig.DATABASE_PATH)
        pass
