#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

from shopdb.api import db
from shopdb.models import Rank, User
from tests.base_api import BaseAPITestCase


class ListUsersAPITestCase(BaseAPITestCase):
    def test_list_users_as_user_and_external(self):
        """Get a list of all users as user and as external."""
        # Set user 3 inactive
        rank = Rank.query.filter(Rank.active.is_(False)).first()
        User.query.filter_by(id=3).first().set_rank_id(rank.id, 1)
        # Make user 2 a system user
        db.session.add(Rank(name="System", is_system_user=True))
        db.session.flush()
        rank = Rank.query.filter(Rank.is_system_user.is_(True)).first()
        User.query.filter_by(id=2).first().set_rank_id(rank.id, 1)
        db.session.commit()

        # Make sure user 3 is inactive and user 4 is a system user
        self.assertFalse(User.query.filter_by(id=3).first().active)
        self.assertTrue(User.query.filter_by(id=2).first().is_system_user)

        for role in ["user", None]:
            res = self.get(url="/users", role=role)
            self.assertEqual(res.status_code, 200)
            users = json.loads(res.data)
            self.assertEqual(len(users), 2)
            user = users[0]
            self.assertEqual(len(user), 6)
            for item in [
                "id",
                "firstname",
                "lastname",
                "fullname",
                "rank_id",
                "imagename",
            ]:
                assert item in user

    def test_list_users_with_token(self):
        """Get a list of all users as admin. It should contain more information
        than the list which gets returned without a token in the request
        header.
        """
        res = self.get(url="/users", role="admin")
        self.assertEqual(res.status_code, 200)
        users = json.loads(res.data)
        self.assertEqual(len(users), 5)
        for user in users:
            self.assertEqual(len(user), 12)
            for item in [
                "id",
                "firstname",
                "lastname",
                "fullname",
                "credit",
                "rank_id",
                "imagename",
                "active",
                "is_admin",
                "creation_date",
                "verification_date",
                "is_verified",
            ]:
                assert item in user
