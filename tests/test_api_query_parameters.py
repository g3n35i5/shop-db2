#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json
from shopdb.api import app
from shopdb.models import Purchase


class QueryParametersAPITestCase(BaseAPITestCase):
    def test_query_parameters_ordering(self):
        """
        Test query ordering
        """
        # List all users ordered by their id in descending order
        users = json.loads(self.get('/users', role='admin', params={"sort": {"field": "id", "order": "DESC"}}).data)
        # There should be 4 ordered by their ids in descending order
        self.assertEqual([4, 3, 2, 1], list(map(lambda x: x['id'], users)))

        # List all users ordered by their firstname in ascending order
        users = json.loads(self.get('/users', role='admin', params={"sort": {"field": "firstname", "order": "ASC"}}).data)
        # There should be 4 ordered by their firstname in ascending order
        self.assertEqual(['Bryce', 'Daniel', 'Mary', 'William'], list(map(lambda x: x['firstname'], users)))

    def test_query_parameters_filter(self):
        """
        Test query filter with a single and multiple values
        """
        # List all users filtered by the lastname 'Smith'
        users = json.loads(self.get('/users', role='admin', params={'filter': {'lastname': 'Smith'}}).data)
        # There should be only 'Mary Smith' with the id 2
        self.assertEqual(1, len(users))
        self.assertEqual('Smith', users[0]['lastname'])
        self.assertEqual('Mary', users[0]['firstname'])
        self.assertEqual(2, users[0]['id'])

        # List all users filtered by two lastnames 'Smith' and 'Lee'
        users = json.loads(self.get('/users', role='admin', params={'filter': {'lastname': ['Smith', 'Lee']}}).data)
        # There should be two users
        self.assertEqual(2, len(users))
        self.assertEqual('Smith', users[0]['lastname'])
        self.assertEqual('Mary', users[0]['firstname'])
        self.assertEqual(2, users[0]['id'])
        self.assertEqual('Lee', users[1]['lastname'])
        self.assertEqual('Daniel', users[1]['firstname'])
        self.assertEqual(4, users[1]['id'])

    def test_query_parameters_pagination(self):
        """
        Test query pagination
        """
        # List all users with the pagination {'page': 1, 'perPage': 1}
        users = json.loads(self.get('/users', role='admin', params={'pagination': {'page': 1, 'perPage': 1}}).data)
        # There should be exactly 1 user (default ordering is [id, ASC] so its the first user)
        self.assertEqual([1], list(map(lambda x: x['id'], users)))

        # List all users with the pagination {'page': 1, 'perPage': 3}
        users = json.loads(self.get('/users', role='admin', params={'pagination': {'page': 1, 'perPage': 3}}).data)
        # There should be exactly 3 users
        self.assertEqual(3, len(users))
        self.assertEqual([1, 2, 3], list(map(lambda x: x['id'], users)))

        # List all users with the pagination {'page': 2, 'perPage': 2}
        users = json.loads(self.get('/users', role='admin', params={'pagination': {'page': 2, 'perPage': 2}}).data)
        # There should be exactly 2 users
        self.assertEqual(2, len(users))
        self.assertEqual([3, 4], list(map(lambda x: x['id'], users)))

    def test_invalid_query_parameters(self):
        """
        This test ensures that only valid query parameters are accepted by the API
        """
        param_list = [
            # Invalid sort column foo
            {"sort": {"field": "foo", "order": "DESC"}, "pagination": {'page': 1, 'perPage': 1}},
            # Invalid sort column password
            {"sort": {"field": "password", "order": "DESC"}, "pagination": {'page': 1, 'perPage': 1}},
            # Invalid parameter "foo"
            {"sort": {"field": "id", "order": "DESC"}, "pagination": {'page': 1, 'perPage': 1}, "foo": "bar"},
            # Second pagination parameter is a string
            {"sort": {"field": "id", "order": "DESC"}, "pagination": {'page': 1, 'perPage': "1"}},
            # Invalid pagination (page 0)
            {"sort": {"field": "id", "order": "DESC"}, "pagination": {'page': 0, 'perPage': 1}},
            # Invalid pagination (both negative)
            {"sort": {"field": "id", "order": "DESC"}, "pagination": {'page': -1, 'perPage': -1}},
            # Invalid pagination (second negative)
            {"sort": {"field": "id", "order": "DESC"}, "pagination": {'page': 1, 'perPage': -1}},
            # Invalid character "!" in filter value
            {"sort": {"field": "id", "order": "DESC"}, "pagination": {'page': 1, 'perPage': 1}, "filter": {'firstname': 'Inval!d value'}},
            # Little Bobby Tables
            {"sort": {"field": "id", "order": "DESC"}, "pagination": {'page': 1, 'perPage': 1}, "filter": {'firstname': 'Robert\'); DROP TABLE users;--'}},
        ]
        for params in param_list:
            res = self.get('/users', params=params)
            self.assertException(res, exc.InvalidQueryParameters())
