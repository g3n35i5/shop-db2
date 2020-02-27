#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
from shopdb.api import db
import shopdb.exceptions as exc
from tests.base import u_passwords, u_firstnames, u_lastnames
from tests.base_api import BaseAPITestCase
from flask import json
import jwt


class LoginAPITestCase(BaseAPITestCase):
    def test_login_user(self):
        """This test is designed to test the login of an existing user with
           an id and password"""
        data = {
            'id': 1,
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

    def test_login_non_verified_user(self):
        """If an authentication attempt is made by a non verified user,
           the correct error message must be returned."""
        # Create a new user.
        data = {
            'firstname': 'John',
            'lastname': 'Doe',
            'password': 'supersecret',
            'password_repeat': 'supersecret'
        }
        res = self.post(url='/register', data=data)

        # Login.
        data = {
            'id': 6,
            'password': 'supersecret'
        }
        res = self.post(url='/login', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsNotVerified)

    def test_login_as_inactive_user(self):
        """
        If an authentication attempt is made by an inactive user,
        the correct error message must be returned."""
        User.query.filter_by(id=1).first().set_rank_id(4, 1)
        db.session.commit()
        data = {'id': 1, 'password': u_passwords[0]}
        res = self.post(url='/login', data=data)
        self.assertException(res, exc.UserIsInactive)

    def test_login_missing_password(self):
        """If an authentication attempt is made without a password,
           the correct error message must be returned."""
        data = {
            'id': 1
        }
        res = self.post(url='/login', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        data = json.loads(res.data)
        assert 'token' not in data

    def test_login_missing_id(self):
        """If an authentication attempt is made without an id,
        the correct error message must be returned."""
        data = {
            'password': u_passwords[0]
        }
        res = self.post(url='/login', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        data = json.loads(res.data)
        assert 'token' not in data

    def test_login_wrong_id(self):
        """If an authentication attempt is made with a wrong id,
           the correct error message must be returned."""
        data = {
            'id': 42,
            'password': u_passwords[0]
        }
        res = self.post(url='/login', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidCredentials)
        data = json.loads(res.data)
        assert 'token' not in data

    def test_login_user_without_password(self):
        """If an authentication attempt is made by a user who has not set
        a password yet, the correct error message must be returned."""

        data = {'id': 3, 'password': 'DontCare'}
        res = self.post(url='/login', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidCredentials)
        data = json.loads(res.data)
        assert 'token' not in data

    def test_login_wrong_password(self):
        """If an authentication attempt is made with a password,
           the correct error message must be returned."""
        data = {
            'id': 1,
            'password': 'my_super_wrong_password'
        }
        res = self.post(url='/login', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidCredentials)
        data = json.loads(res.data)
        assert 'token' not in data
