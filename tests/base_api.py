#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import sys
import urllib

from flask import json

from tests.base import BaseTestCase, u_passwords


class BaseAPITestCase(BaseTestCase):
    def assertException(self, res, exception):
        """This helper function checks whether the correct exception has
           been raised"""
        data = json.loads(res.data)
        self.assertEqual(res.status_code, exception.code)
        self.assertEqual(data['message'], exception.message)
        self.assertEqual(data['result'], exception.type)

    def _request(self, type, url, data, role, content_type, params=None):
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
            if params is not None:
                params = urllib.parse.urlencode(params)
            res = self.client.get(url, data=data, headers=headers, query_string=params)
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

    def get(self, url, data=None, role=None, params=None,
            content_type='application/json'):
        """Helper function to perform a GET request to the API"""
        return self._request(type='GET', url=url, data=data, role=role,
                             params=params, content_type=content_type)

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
