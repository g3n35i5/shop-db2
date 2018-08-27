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

    def test_promote_user_to_admin(self):
        '''Update the admin state of a user.'''
        self.assertFalse(User.query.filter_by(id=2).first().is_admin)
        data = {'is_admin': True}
        res = self.put(url='/users/2', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Updated user.')
        self.assertEqual(data['updated_fields'], ['is_admin'])
        self.assertTrue(User.query.filter_by(id=2).first().is_admin)

    def test_promote_user_to_admin_twice(self):
        '''When a user gets promoted to an admin twice, nothing
           should change.'''
        self.assertTrue(User.query.filter_by(id=1).first().is_admin)
        data = {'is_admin': True}
        res = self.put(url='/users/1', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        self.assertTrue(User.query.filter_by(id=1).first().is_admin)

    def test_update_forbidden_field(self):
        '''Updating a forbidden field should raise an error.'''
        self.assertEqual(User.query.filter_by(id=1).first().credit, 0)
        data = {'credit': 10000}
        res = self.put(url='/users/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)
        self.assertEqual(User.query.filter_by(id=1).first().credit, 0)

    def test_update_non_existing_user(self):
        '''Updating a non existing user should raise an error.'''
        data = {'firstname': 'Peter'}
        res = self.put(url='/users/5', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserNotFound)

    def test_update_user_password(self):
        '''Update user password'''
        # Login should fail
        data = {
            'email': u_emails[0],
            'password': 'SuperSecret'
        }
        res = self.post(url='/login', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidCredentials)

        # Update password
        data = {'password': 'SuperSecret', 'repeat': 'SuperSecret'}
        res = self.put(url='/users/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)

        # Login should work
        data = {
            'email': u_emails[0],
            'password': 'SuperSecret'
        }
        res = self.post(url='/login', data=data)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert all(item in data for item in ['token', 'result'])
        self.assertTrue(data['result'])

    def test_update_wrong_type(self):
        '''A wrong field type should raise an error'''
        user1 = User.query.filter_by(id=1).first()
        data = {'firstname': True}
        res = self.put(url='/users/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        user2 = User.query.filter_by(id=1).first()
        self.assertEqual(user1, user2)

    def test_update_password_no_repeat(self):
        '''Updating a password without repeat should raise an error'''
        data = {'password': 'SuperSecret'}
        res = self.put(url='/users/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_update_password_wrong_repeat(self):
        '''Updating a password with a wrong repeat should raise an error'''
        data = {'password': 'SuperSecret', 'repeat': 'Super...Ooops'}
        res = self.put(url='/users/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.PasswordsDoNotMatch)

    def test_update_firstname(self):
        '''Update the firstname of a user.'''
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
