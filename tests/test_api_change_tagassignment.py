#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from flask import json

import shopdb.exceptions as exc
from shopdb.api import db
# from shopdb.models import Product, Tag
from shopdb.models.product import Product
from shopdb.models.tag import Tag
from tests.base_api import BaseAPITestCase


class ChangeTagassignmentAPITestCase(BaseAPITestCase):
    def test_change_tag_assignment_authorization(self):
        """This route should only be available for administrators"""
        res = self.post(url='/tagassignment/add', data={})
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url='/tagassignment/add', data={}, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url='/tagassignment/add', data={}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_assign_tag(self):
        """Assign a tag as admin."""
        self.assertEqual(0, len(Product.query.filter_by(id=1).first().tags))
        data = {'product_id': 1, 'tag_id': 1}
        res = self.post(url='/tagassignment/add', role='admin', data=data)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Tag assignment has been added.')
        self.assertEqual(1, len(Product.query.filter_by(id=1).first().tags))

    def test_remove_tag_assignment(self):
        """Remove a tag assignment as admin."""
        product = Product.query.filter_by(id=1).first()
        tag1 = Tag.query.filter_by(id=1).first()
        tag2 = Tag.query.filter_by(id=2).first()
        product.tags.append(tag1)
        product.tags.append(tag2)
        db.session.commit()
        data = {'product_id': 1, 'tag_id': 1}
        res = self.post(url='/tagassignment/remove', role='admin', data=data)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Tag assignment has been removed.')
        self.assertEqual(1, len(Product.query.filter_by(id=1).first().tags))

    def test_assign_tag_wrong_type(self):
        """Assign a tag with a wrong type."""
        data = {'product_id': '1', 'tag_id': 1}
        res = self.post(url='/tagassignment/add', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_assign_tag_missing_data(self):
        """Assign a tag with missing data."""
        data = {'product_id': '1'}
        res = self.post(url='/tagassignment/add', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_assign_tag_invalid_product(self):
        """Assign a tag with an invalid product id."""
        data = {'product_id': 5, 'tag_id': 1}
        res = self.post(url='/tagassignment/add', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_assign_tag_invalid_tag(self):
        """Assign a tag with an invalid tag id."""
        data = {'product_id': 1, 'tag_id': 6}
        res = self.post(url='/tagassignment/add', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_assign_tag_twice(self):
        """Assign a tag which has already been assigned"""
        product = Product.query.filter_by(id=1).first()
        tag = Tag.query.filter_by(id=1).first()
        product.tags.append(tag)
        db.session.commit()
        data = {'product_id': 1, 'tag_id': 1}
        res = self.post(url='/tagassignment/add', role='admin', data=data)
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_remove_tag_twice(self):
        """Remove a tag which has already been removed"""
        data = {'product_id': 1, 'tag_id': 1}
        res = self.post(url='/tagassignment/remove', role='admin', data=data)
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_remove_last_tag(self):
        """Removing the last tag of a product must raise an error"""
        # Assign tag
        product = Product.query.filter_by(id=1).first()
        tag = Tag.query.filter_by(id=1).first()
        product.tags.append(tag)
        db.session.commit()

        data = {'product_id': 1, 'tag_id': 1}
        res = self.post(url='/tagassignment/remove', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.NoRemainingTag)

    def test_assign_tag_unknown_field(self):
        """Unknown fields should raise an exception."""
        data = {'product_id': 1, 'tag_id': 1, 'foo': 42}
        res = self.post(url='/tagassignment/add', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)
        self.assertEqual(0, len(Product.query.filter_by(id=1).first().tags))

    def test_assign_tag_invalid_command(self):
        """
        Invalid command should raise an exception.
        """
        data = {'product_id': 1, 'tag_id': 1, 'foo': 42}
        res = self.post(url='/tagassignment/foo', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        self.assertEqual(0, len(Product.query.filter_by(id=1).first().tags))
