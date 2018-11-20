from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class ChangeTagassignmentAPITestCase(BaseAPITestCase):
    def test_change_tag_assignment_authorization(self):
        """This route should only be available for administrators"""
        res = self.post(url='/tagassignment', data={})
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url='/tagassignment', data={}, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url='/tagassignment', data={}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_assign_tag(self):
        """Assign a tag as admin."""
        self.assertEqual(0, len(Product.query.filter_by(id=1).first().tags))
        data = {'product_id': 1, 'tag_id': 1}
        res = self.post(url='/tagassignment', role='admin', data=data)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Tag assignment has been added.')
        self.assertEqual(1, len(Product.query.filter_by(id=1).first().tags))

    def test_remove_tag_assignment(self):
        """Remove a tag assignment as admin."""
        product = Product.query.filter_by(id=1).first()
        tag = Tag.query.filter_by(id=1).first()
        product.tags.append(tag)
        db.session.commit()
        data = {'product_id': 1, 'tag_id': 1}
        res = self.delete(url='/tagassignment', role='admin', data=data)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Tag assignment has been removed.')
        self.assertEqual(0, len(Product.query.filter_by(id=1).first().tags))

    def test_assign_tag_wrong_type(self):
        """Assign a tag with a wrong type."""
        data = {'product_id': '1', 'tag_id': 1}
        res = self.post(url='/tagassignment', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_assign_tag_missing_data(self):
        """Assign a tag with missing data."""
        data = {'product_id': '1'}
        res = self.post(url='/tagassignment', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_assign_tag_twice(self):
        """Assign a tag which has already been assigned"""
        product = Product.query.filter_by(id=1).first()
        tag = Tag.query.filter_by(id=1).first()
        product.tags.append(tag)
        db.session.commit()
        data = {'product_id': 1, 'tag_id': 1}
        res = self.post(url='/tagassignment', role='admin', data=data)
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_assign_tag_unknown_field(self):
        """Unknown fields should raise an exception."""
        data = {'product_id': 1, 'tag_id': 1, 'foo': 42}
        res = self.post(url='/tagassignment', role='admin', data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)
        self.assertEqual(0, len(Product.query.filter_by(id=1).first().tags))
