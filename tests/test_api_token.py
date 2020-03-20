#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import datetime

import jwt
from flask import json

import shopdb.exceptions as exc
from tests.base import user_data
from tests.base_api import BaseAPITestCase


class TokenAPITestCase(BaseAPITestCase):
    def test_manipulate_token(self):
        """A manipulated/invalid token should raise an error."""
        data = {'id': 1, 'password': user_data[0]['password']}
        res = self.post(url='/login', data=data)
        token = json.loads(res.data)['token']

        # Manipulate token
        token += 'manipulated'
        headers = {'content-type': 'application/json', 'token': token}

        # Do request on a route which requires an admin
        res = self.client.put('/users/2', data=json.dumps({}), headers=headers)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.TokenIsInvalid)

        # Do request on a route which optionally requires an admin
        res = self.client.get('/users', data=json.dumps({}), headers=headers)
        self.assertEqual(res.status_code, 200)

    def test_token_expired(self):
        """An expired token should raise an error."""
        data = {'id': 1, 'password': user_data[0]['password']}
        res = self.post(url='/login', data=data)
        token = json.loads(res.data)['token']

        # Manipulate token
        decode = jwt.decode(token, self.app.config['SECRET_KEY'])
        new_exp = datetime.datetime.now() - datetime.timedelta(minutes=5)
        decode['exp'] = int(round(new_exp.timestamp()))
        new_token = jwt.encode(decode, self.app.config['SECRET_KEY'])
        new_token = new_token.decode('UTF-8')

        # Do request on a route which requires an admin
        headers = {'content-type': 'application/json', 'token': new_token}
        res = self.client.put('/users/2', data=json.dumps({}), headers=headers)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.TokenHasExpired)

        # Do request on a route which optionally requires an admin
        headers = {'content-type': 'application/json', 'token': new_token}
        res = self.client.get('/users', data=json.dumps({}), headers=headers)
        self.assertEqual(res.status_code, 200)

    def test_token_missing_user(self):
        """Each token contains a user dictionary. If it is missing, an error
           should be raised."""
        data = {'id': 1, 'password': user_data[0]['password']}
        res = self.post(url='/login', data=data)
        token = json.loads(res.data)['token']

        # Manipulate token
        decode = jwt.decode(token, self.app.config['SECRET_KEY'])
        del decode['user']
        token = jwt.encode(decode, self.app.config['SECRET_KEY'])

        # Do request on a route which requires an admin
        headers = {'content-type': 'application/json', 'token': token}
        res = self.client.put('/users/2', data=json.dumps({}), headers=headers)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.TokenIsInvalid)

        # Do request on a route which optionally requires an admin
        headers = {'content-type': 'application/json', 'token': token}
        res = self.client.get('/users', data=json.dumps({}), headers=headers)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.TokenIsInvalid)
