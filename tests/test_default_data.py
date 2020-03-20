#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.api import bcrypt
from shopdb.models import User, Rank
from tests.base import BaseTestCase
from tests.base import user_data, rank_data


class DefaultDataTest(BaseTestCase):
    def test_default_users(self):
        """Check if all users have been entered correctly"""
        users = User.query.all()
        # Check number of users
        self.assertEqual(len(users), len(user_data))

        for index, data in enumerate(user_data):
            self.assertEqual(users[index].firstname, data['firstname'])
            self.assertEqual(users[index].lastname, data['lastname'])
            if data['password']:
                self.assertTrue(bcrypt.check_password_hash(users[index].password, data['password']))

    def test_insert_default_ranks(self):
        """Check if all ranks have been entered correctly"""
        ranks = Rank.query.all()
        self.assertEqual(len(ranks), len(rank_data))
        for index, rank in enumerate(ranks):
            self.assertEqual(rank.name, rank_data[index]['name'])
            self.assertEqual(rank.id, index + 1)

    def test_verify_all_users_except_last(self):
        """Check if all users except the last one have been verified"""
        users = User.query.all()
        self.assertEqual(users[0].rank_id, 2)
        self.assertEqual(users[1].rank_id, 3)
        self.assertEqual(users[2].rank_id, 1)
        self.assertFalse(users[3].is_verified)
        self.assertEqual(users[4].rank_id, 1)
