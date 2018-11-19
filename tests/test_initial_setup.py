#!/usr/bin/env python3

from shopdb.api import *
from shopdb.models import *
from flask_testing import TestCase
import configuration as config
from flask import json
import sys

class InitialSetupTestCase(TestCase):
    def create_app(self):
        app.config.from_object(config.UnittestConfig)
        return app

    def setUp(self):
        # Create tables
        db.create_all()
        db.session.commit()
        # Create test client
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def assertException(self, res, exception):
        """This helper function checks whether the correct exception has
           been raised"""
        data = json.loads(res.data)
        self.assertEqual(res.status_code, exception.code)
        self.assertEqual(data['message'], exception.message)
        self.assertEqual(data['result'], exception.type)

    def _request(self, type, url, data, role, content_type):
        """Helper function to perform a request to the API"""
        if role not in ['admin', 'user', None]:  # pragma: no cover
            sys.exit(f'Wrong role: {role}')

        # Only serialize the data to JSON if it is a json object.
        if content_type == 'application/json':
            data = json.dumps(data)

        headers = {'content-type': content_type}
        if type == 'POST':
            res = self.client.post(url, data=data, headers=headers)
        elif type == 'PUT':
            res = self.client.put(url, data=data, headers=headers)
        elif type == 'GET':
            res = self.client.get(url, data=data, headers=headers)
        elif type == 'DELETE':
            res = self.client.delete(url, data=data, headers=headers)
        else:  # pragma: no cover
            sys.exit('Wrong request type: {}'.format(type))

        return res

    def post(self, url, data=None, role=None,
             content_type='application/json'):
        """Helper function to perform a POST request to the API"""
        return self._request(type='POST', url=url, data=data, role=role,
                             content_type=content_type)

    def login(self, id, password):
        """Helper function to perform a login"""
        data = {'id': id, 'password': password}
        return self.client.post('/login', data=json.dumps(data),
                                headers={'content-type': 'application/json'})

    def test_initial_setup(self):
        """Test the initial setup"""
        data = {'user': {'firstname': 'User', 'lastname': 'One',
                         'password': 'passwd', 'password_repeat': 'passwd'},
                'INIT_TOKEN': 'INIT'}
        res = self.post(url='/initial_setup', data=data, role=None)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['message'],
                              'shop.db was successfully initialized')

    def test_initial_setup_existing_user(self):
        """With an existing user, an error should be raised"""
        user = User(firstname='User', lastname='Zero', password='wfhgpiurewqnb')
        db.session.add(user)
        db.session.commit()
        data = {'user': {'firstname': 'User', 'lastname': 'One',
                         'password': 'passwd', 'password_repeat': 'passwd'},
                'INIT_TOKEN': 'INIT'}
        res = self.post(url='/initial_setup', data=data, role=None)
        self.assertEqual(res.status_code, 401)
        data = json.loads(res.data)
        self.assertException(res, exc.UnauthorizedAccess())

    def test_initial_setup_missing_data(self):
        """With missing data, an error should be raised"""
        data = {'user': {'firstname': 'User', 'lastname': 'One',
                         'password': 'passwd', 'password_repeat': 'passwd'}}
        res = self.post(url='/initial_setup', data=data, role=None)
        self.assertEqual(res.status_code, 401)
        data = json.loads(res.data)
        self.assertException(res, exc.DataIsMissing())

    def test_initial_setup_wrong_token(self):
        """With wrong init token, an error should be raised"""
        data = {'user': {'firstname': 'User', 'lastname': 'One',
                         'password': 'passwd', 'password_repeat': 'passwd'},
                'INIT_TOKEN': 'foo'}
        res = self.post(url='/initial_setup', data=data, role=None)
        self.assertEqual(res.status_code, 401)
        data = json.loads(res.data)
        self.assertException(res, exc.UnauthorizedAccess())
