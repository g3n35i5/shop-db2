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


class UpdateUserAPITestCase(BaseAPITestCase):
    def test_update_authorization(self):
        '''This route should only be available for adminisrators'''
        res = self.put(url='/users/2', data={})
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.put(url='/users/2', data={}, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.put(url='/users/2', data={}, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_update_firstname(self):
        '''Update the firstname of a user'''
        user = User.query.filter(User.id == 2).first()
        self.assertEqual(user.firstname, 'Mary')
        data = {'firstname': 'New-Mary'}
        res = self.put(url='/users/2', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Updated user.')
        self.assertEqual(data['updated_fields'], ['firstname'])
        user = User.query.filter(User.id == 2).first()
        self.assertEqual(user.firstname, 'New-Mary')
