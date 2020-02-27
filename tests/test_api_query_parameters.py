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
        self.assertEqual([5, 4, 3, 2, 1], list(map(lambda x: x['id'], users)))

        # List all users ordered by their firstname in ascending order
        users = json.loads(self.get('/users', role='admin', params={"sort": {"field": "firstname", "order": "ASC"}}).data)
        # There should be 5 ordered by their firstname in ascending order
        self.assertEqual([None, 'Bryce', 'Daniel', 'Mary', 'William'], list(map(lambda x: x['firstname'], users)))

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

        # List by boolean values
        users = json.loads(self.get('/users', role='admin', params={'filter': {'is_verified': False}}).data)
        self.assertEqual(1, len(users))
        self.assertEqual('Lee', users[0]['lastname'])
        self.assertEqual('Daniel', users[0]['firstname'])

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

        # List all users with the rank_id 1
        users = json.loads(self.get('/users', role='admin', params={'filter': {'rank_id': 1}}).data)
        # There should only be Bryce Jones
        self.assertEqual(2, len(users))
        self.assertEqual('Jones', users[0]['lastname'])
        self.assertEqual('Bryce', users[0]['firstname'])
        self.assertEqual('Seller', users[1]['lastname'])
        self.assertEqual(None, users[1]['firstname'])

        # Use two filters for firstname and lastname
        params = {'filter': {'lastname': ['Smith', 'Lee'], 'firstname': 'Mary'}}
        users = json.loads(self.get('/users', role='admin', params=params).data)
        # There should only be Mary Smith
        self.assertEqual(1, len(users))
        self.assertEqual('Smith', users[0]['lastname'])
        self.assertEqual('Mary', users[0]['firstname'])

        # If we add another filter with ids, there should still be only Mary
        params = {'filter': {'lastname': ['Smith', 'Lee'], 'firstname': 'Mary', 'id': [2, 3]}}
        users = json.loads(self.get('/users', role='admin', params=params).data)
        # There should only be Mary Smith
        self.assertEqual(1, len(users))
        self.assertEqual('Smith', users[0]['lastname'])
        self.assertEqual('Mary', users[0]['firstname'])

        # By removing her id from the filter, no user should be found
        params = {'filter': {'lastname': ['Smith', 'Lee'], 'firstname': 'Mary', 'id': 3}}
        users = json.loads(self.get('/users', role='admin', params=params).data)
        # There shouldn't be any results
        self.assertEqual(0, len(users))

    def test_query_parameters_sorting(self):
        """
        Test query sorting
        """
        # List all users and sort them by their firstname
        params = {'sort': {'field': 'firstname', 'order': 'ASC'}}
        users = json.loads(self.get('/users', role='admin', params=params).data)
        self.assertEqual([None, 'Bryce', 'Daniel', 'Mary', 'William'], list(map(lambda x: x['firstname'], users)))

        # Insert default purchases so that the user credits change
        self.insert_default_purchases()
        # List all users and sort them by their credit
        params = {'sort': {'field': 'credit', 'order': 'ASC'}}
        users = json.loads(self.get('/users', role='admin', params=params).data)
        self.assertEqual([-1800, -1100, -400, 0, 0], list(map(lambda x: x['credit'], users)))


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
            # Multiple filters with one invalid type
            {"sort": {"field": "id", "order": "DESC"}, "pagination": {'page': 1, 'perPage': 1},
             "filter": {'firstname': 'Mary', 'id': [1, 2, 3, "4"], 'lastname': 'Smith'}},
        ]
        for params in param_list:
            res = self.get('/users', params=params)
            self.assertException(res, exc.InvalidQueryParameters())
