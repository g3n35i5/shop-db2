from shopdb.api import *
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
        p_data = {'name': 'CoolTag'}

        res = self.post(url='/tags', role='admin', data=p_data)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Created Tag.')
        tag = Tag.query.filter_by(name='CoolTag').first()
        for field in p_data:
            self.assertEqual(getattr(tag, field), p_data[field])
        self.assertEqual(tag.created_by, 1)

    def test_create_tag_wrong_type(self):
        """Create a tag as admin with wrong type(s)."""
        data = {'name': 1234.0}
        res = self.post(url='/tags', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        self.assertEqual(len(Tag.query.all()), 4)

    def test_create_product_missing_name(self):
        """Create a tag as admin with missing name."""
        data = {}
        res = self.post(url='/tags', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        self.assertFalse(Tag.query.filter_by(id=5).first())

    def test_create_tag_already_existing(self):
        """Creating a tag which already exists should not be possible."""
        data = {'name': 'Coffee'}
        res = self.post(url='/tags', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryAlreadyExists)
        self.assertFalse(Tag.query.filter_by(id=5).first())

    def test_create_tag_unknown_field(self):
        """Unknown fields should raise an exception."""
        data = {'name': 'Bread', 'price': 100}
        res = self.post(url='/tags', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)
        self.assertFalse(Tag.query.filter_by(id=5).first())
