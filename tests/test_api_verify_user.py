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


class VerifyUserAPITestCase(BaseAPITestCase):
    def test_verify_user(self):
        """Test verifying a user."""
        user = User.query.filter_by(id=4).first()
        self.assertFalse(user.is_verified)
        data = {'rank_id': 1}
        res = self.post(url='/verify/4', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        user = User.query.filter_by(id=4).first()
        self.assertTrue(user.is_verified)

    def test_verify_user_twice(self):
        """Test verifying a user twice."""
        user = User.query.filter_by(id=2).first()
        self.assertTrue(user.is_verified)
        data = {'rank_id': 1}
        res = self.post(url='/verify/2', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserAlreadyVerified)

    def test_verify_non_existing_user(self):
        """Test verifying a non existing user."""
        data = {'rank_id': 1}
        res = self.post(url='/verify/5', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserNotFound)
