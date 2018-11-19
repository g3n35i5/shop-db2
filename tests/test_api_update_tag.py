from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class UpdateTagAPITestCase(BaseAPITestCase):
    def test_update_authorization(self):
        """This route should only be available for administrators"""
        res = self.put(url='/tags/2', data={})
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.put(url='/tags/2', data={}, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.put(url='/tags/2', data={}, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_update_forbidden_field(self):
        """Updating a forbidden field should raise an error."""
        self.assertTrue(Product.query.filter_by(id=1).first().countable)
        data = {'created_by': 2}
        res = self.put(url='/products/2', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)
        self.assertEqual(Tag.query.filter_by(id=2).first().created_by, 1)

    def test_update_non_existing_tag(self):
        """Updating a non existing tag should raise an error."""
        data = {'name': 'Foo'}
        res = self.put(url='/tags/5', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.TagNotFound)

    def test_update_wrong_type(self):
        """A wrong field type should raise an error"""
        tag1 = Tag.query.filter_by(id=1).first()
        data = {'name': True}
        res = self.put(url='/tags/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        tag2 = Tag.query.filter_by(id=1).first()
        self.assertEqual(tag1, tag2)

    def test_update_unknown_field(self):
        """An unknown field should raise an error"""
        data = {'color': 'red'}
        res = self.put(url='/tags/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_tag_name(self):
        """Update tag name"""
        self.assertEqual(Tag.query.filter_by(id=1).first().name, 'Food')
        data = {'name': 'Foo'}
        res = self.put(url='/tags/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Updated tag.')
        self.assertEqual(len(data['updated_fields']), 1)
        self.assertEqual(data['updated_fields'][0], 'name')
        self.assertEqual(Tag.query.filter_by(id=1).first().name, 'Foo')
