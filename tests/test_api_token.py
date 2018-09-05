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
import datetime


class TokenAPITestCase(BaseAPITestCase):
    def test_manipulate_token(self):
        '''A manipulated/invalid token should raise an error.'''
        data = {'identifier': u_usernames[0], 'password': u_passwords[0]}
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
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.TokenIsInvalid)

    def test_token_expired(self):
        '''An expired token should raise an error.'''
        data = {'identifier': u_usernames[0], 'password': u_passwords[0]}
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
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.TokenHasExpired)

    def test_token_missing_user(self):
        '''Each token contains a user dictionary. If it is missing, an error
           should be raised.'''
        data = {'identifier': u_usernames[0], 'password': u_passwords[0]}
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
