#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class CreateTagAPITestCase(BaseAPITestCase):
    def test_create_tag_authorization(self):
        """This route should only be available for administrators"""
        res = self.post(url='/tags', data={})
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url='/tags', data={}, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url='/tags', data={}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_tag(self):
        """Create a tag as admin."""

        tag_data_list = [{'name': 'CoolTag'}, {'name': 'CoolTag2', 'is_for_sale': False}]

        for index, t_data in enumerate(tag_data_list):
            res = self.post(url='/tags', role='admin', data=t_data)
            self.assertEqual(res.status_code, 201)
            data = json.loads(res.data)
            self.assertEqual(data['message'], 'Created Tag.')
            tag = Tag.query.filter_by(name=t_data['name']).first()
            self.assertEqual(tag.created_by, 1)

        self.assertTrue(db.session.query(Tag).filter(Tag.name == tag_data_list[0]['name']).first().is_for_sale)
        self.assertFalse(db.session.query(Tag).filter(Tag.name == tag_data_list[1]['name']).first().is_for_sale)

    def test_create_tag_wrong_type(self):
        """Create a tag as admin with wrong type(s)."""
        data = {'name': 1234.0}
        res = self.post(url='/tags', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        self.assertEqual(len(Tag.query.all()), 5)

    def test_create_product_missing_name(self):
        """Create a tag as admin with missing name."""
        data = {}
        res = self.post(url='/tags', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        self.assertFalse(Tag.query.filter_by(id=6).first())

    def test_create_tag_already_existing(self):
        """Creating a tag which already exists should not be possible."""
        data = {'name': 'Coffee'}
        res = self.post(url='/tags', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryAlreadyExists)
        self.assertFalse(Tag.query.filter_by(id=6).first())

    def test_create_tag_unknown_field(self):
        """Unknown fields should raise an exception."""
        data = {'name': 'Bread', 'price': 100}
        res = self.post(url='/tags', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)
        self.assertFalse(Tag.query.filter_by(id=6).first())
