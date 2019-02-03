from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class DeleteTagAPITestCase(BaseAPITestCase):
    def test_delete_tag_authorization(self):
        """This route should only be available for administrators"""
        res = self.delete(url='/tags/1', data={})
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.delete(url='/tags/1', data={}, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_delete_tag(self):
        """Delete a tag as admin."""
        res = self.delete(url='/tags/1', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Tag deleted.')
        tag = Tag.query.filter_by(id=1).first()
        self.assertEqual(tag, None)

    def test_delete_assigned_tag(self):
        """
        If a tag that is already assigned to products is deleted, it must be
        checked whether it also disappears from the list of tags.
        """
        product1 = Product.query.filter_by(id=1).first()
        product2 = Product.query.filter_by(id=2).first()
        tag = Tag.query.filter_by(id=1).first()
        product1.tags.append(tag)
        product2.tags.append(tag)
        db.session.commit()
        product1 = Product.query.filter_by(id=1).first()
        product2 = Product.query.filter_by(id=2).first()
        self.assertEqual(len(product1.tags), 1)
        self.assertEqual(len(product2.tags), 1)
        self.delete(url='/tags/1', role='admin')
        product1 = Product.query.filter_by(id=1).first()
        product2 = Product.query.filter_by(id=2).first()
        self.assertEqual(len(product1.tags), 0)
        self.assertEqual(len(product2.tags), 0)

    def test_delete_non_existing_tag(self):
        """Delete a non existing tag."""
        res = self.delete(url='/tags/5', role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_delete_last_tag_in_database(self):
        """It should not be possible to delete the last remaining tag."""
        tags = Tag.query.all()
        for i in range(3):
            db.session.delete(tags[i])
        db.session.commit()

        res = self.delete(url='/tags/4', role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.NoRemainingTag)
