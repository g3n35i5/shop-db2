import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class GetTagAPITestCase(BaseAPITestCase):
    def test_get_single_tag(self):
        """Test for getting a single tag"""
        res = self.get(url='/tags/1')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'tag' in data
        self.assertEqual(data['tag']['id'], 1)
        self.assertEqual(data['tag']['name'], 'Food')
        self.assertEqual(data['tag']['created_by'], 1)

    def test_get_non_existing_tag(self):
        """Getting a non existing tag should raise an error."""
        res = self.get(url='/tags/5')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.TagNotFound)
