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


class ListUsersAPITestCase(BaseAPITestCase):
    def test_list_users_without_token(self):
        '''Get a list of all users as user'''
        res = self.get(url='/users')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'users' in data
        users = data['users']
        self.assertEqual(len(users), 3)
        for user in users:
            self.assertEqual(len(user), 4)
            for item in ['id', 'firstname', 'lastname', 'username']:
                assert item in user

    def test_list_users_with_token(self):
        '''Get a list of all users as admin. It should contain more information
           than the list which gets returned without a token in the request
           header.'''
        res = self.get(url='/users', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'users' in data
        users = data['users']
        self.assertEqual(len(users), 3)
        for user in users:
            self.assertEqual(len(user), 6)
            for item in ['id', 'firstname', 'lastname',
                         'username', 'email', 'credit']:
                assert item in user
