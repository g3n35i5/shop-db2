#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
from shopdb.api import bcrypt
from tests.base import BaseTestCase
from tests.base import u_passwords, u_firstnames, u_lastnames, rank_data


class DefaultDataTest(BaseTestCase):
    def test_default_users(self):
        """Check if all users have been entered correctly"""
        users = User.query.all()
        # Check number of users
        self.assertEqual(len(users), len(u_firstnames))

        for i in range(0, len(u_firstnames)):
            self.assertEqual(users[i].firstname, u_firstnames[i])
            self.assertEqual(users[i].lastname, u_lastnames[i])
            if u_passwords[i]:
                self.assertTrue(bcrypt.check_password_hash(
                    users[i].password, u_passwords[i]))

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
