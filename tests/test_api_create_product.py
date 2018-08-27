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


class CreateProductsAPITestCase(BaseAPITestCase):
    def test_create_product_authorization(self):
        '''This route should only be available for adminisrators'''
        res = self.post(url='/products', data={})
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url='/products', data={}, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url='/products', data={}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_product(self):
        '''Create a Product as admin.'''
        p_data = {
            'name': 'Bread', 'price': 100,
            'barcode': '12345678', 'active': True,
            'countable': True, 'revokable': True,
            'imagename': 'bread.png'}

        res = self.post(url='/products', role='admin', data=p_data)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Created Product.')
        product = Product.query.filter_by(name='Bread').first()
        for field in p_data:
            self.assertEqual(getattr(product, field), p_data[field])

    def test_create_product_wrong_type(self):
        '''Create a Product as admin with wrong type(s).'''
        p_data = {
            'name': 'Bread', 'price': 100,
            'barcode': '12345678', 'active': True,
            'countable': True, 'revokable': True,
            'imagename': 'bread.png'}

        for field in p_data:
            copy_data = copy(p_data)
            copy_data[field] = 100.0
            res = self.post(url='/products', role='admin', data=copy_data)
            self.assertEqual(res.status_code, 401)
            self.assertException(res, exc.WrongType)

        self.assertEqual(len(Product.query.all()), 4)

    def test_create_product_missing_name(self):
        '''Create a Product as admin with missing name.'''
        data = {'price': 100}
        res = self.post(url='/products', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        self.assertFalse(Product.query.filter_by(id=5).first())

    def test_create_product_missing_price(self):
        '''Create a Product as admin with missing price.'''
        data = {'name': 'Bread'}
        res = self.post(url='/products', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        self.assertFalse(Product.query.filter_by(id=5).first())

    def test_create_product_already_existing(self):
        '''Creating a product which already exists should not be possible.'''
        data = {'name': 'Pizza', 'price': 300}
        res = self.post(url='/products', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ProductAlreadyExists)
        self.assertFalse(Product.query.filter_by(id=5).first())

    def test_create_product_unknown_field(self):
        '''Unknown fields should raise an exception.'''
        data = {'name': 'Bread', 'price': 100, 'color': 'blue'}
        res = self.post(url='/products', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)
