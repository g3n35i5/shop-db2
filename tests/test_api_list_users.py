#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
from shopdb.api import db
from tests.base_api import BaseAPITestCase
from flask import json


class ListUsersAPITestCase(BaseAPITestCase):
    def test_list_users_as_user_and_external(self):
        """Get a list of all users as user and as external."""

        # Set user 3 inactive
        rank = Rank.query.filter(Rank.active.is_(False)).first()
        User.query.filter_by(id=3).first().set_rank_id(rank.id, 1)
        db.session.commit()
        self.assertFalse(User.query.filter_by(id=3).first().active)
        for role in ['user', None]:
            res = self.get(url='/users', role=role)
            self.assertEqual(res.status_code, 200)
            users = json.loads(res.data)
            self.assertEqual(len(users), 2)
            for user in users:
                self.assertEqual(len(user), 4)
                for item in ['id', 'firstname', 'lastname', 'rank_id']:
                    assert item in user

    def test_list_users_with_token(self):
        """Get a list of all users as admin. It should contain more information
           than the list which gets returned without a token in the request
           header."""
        res = self.get(url='/users', role='admin')
        self.assertEqual(res.status_code, 200)
        users = json.loads(res.data)
        self.assertEqual(len(users), 3)
        for user in users:
            self.assertEqual(len(user), 7)
            for item in ['id', 'firstname', 'lastname', 'creation_date',
                         'credit', 'is_admin', 'rank_id']:
                assert item in user

