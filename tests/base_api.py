#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import sys
import urllib

from flask import json

from tests.base import BaseTestCase, user_data


class BaseAPITestCase(BaseTestCase):
    def assertException(self, res, exception):
        """This helper function checks whether the correct exception has
           been raised"""
        data = json.loads(res.data)
        self.assertEqual(res.status_code, exception.code)
        self.assertEqual(data['message'], exception.message)
        self.assertEqual(data['result'], exception.type)

    def _request(self, request_type, url, data, role, content_type, params=None):
        """Helper function to perform a request to the API"""
        if role not in ['admin', 'user', None]:  # pragma: no cover
            sys.exit(f'Wrong role: {role}')

        if role == 'admin':
            user_id = 1
            password = user_data[0]['password']
        elif role == 'user':
            user_id = 2
            password = user_data[1]['password']
        else:
            user_id = None
            password = None

        # Only serialize the data to JSON if it is a json object.
        if content_type == 'application/json':
            data = json.dumps(data)

        headers = {'content-type': content_type}
        if user_id and password:
            res = self.login(user_id, password)
            headers['token'] = json.loads(res.data)['token']
        if request_type == 'POST':
            res = self.client.post(url, data=data, headers=headers)
        elif request_type == 'PUT':
            res = self.client.put(url, data=data, headers=headers)
        elif request_type == 'GET':
            if params is not None:
                params = urllib.parse.urlencode(params)
            res = self.client.get(url, data=data, headers=headers, query_string=params)
        elif request_type == 'DELETE':
            res = self.client.delete(url, data=data, headers=headers)
        else:  # pragma: no cover
            sys.exit('Wrong request type: {}'.format(request_type))

        return res

    def post(self, url, data=None, role=None,
             content_type='application/json'):
        """Helper function to perform a POST request to the API"""
        return self._request(request_type='POST', url=url, data=data, role=role,
                             content_type=content_type)

    def get(self, url, data=None, role=None, params=None,
            content_type='application/json'):
        """Helper function to perform a GET request to the API"""
        return self._request(request_type='GET', url=url, data=data, role=role,
                             params=params, content_type=content_type)

    def put(self, url, data=None, role=None,
            content_type='application/json'):
        """Helper function to perform a GET request to the API"""
        return self._request(request_type='PUT', url=url, data=data, role=role,
                             content_type=content_type)

    def delete(self, url, data=None, role=None,
               content_type='application/json'):
        """Helper function to perform a DELETE request to the API"""
        return self._request(request_type='DELETE', url=url, data=data, role=role,
                             content_type=content_type)

    def login(self, user_id: int, password: str):
        """Helper function to perform a login"""
        data = {'id': user_id, 'password': password}
        return self.client.post('/login', data=json.dumps(data),
                                headers={'content-type': 'application/json'})
