import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class MiscAPITestCase(BaseAPITestCase):
    def test_empty_json(self):
        """An empty json body should raise an error."""
        res = self.client.post('/login', data=None)
        self.assertException(res, exc.InvalidJSON)

    def test_get_api_root(self):
        """An empty json body should raise an error."""
        res = self.client.get('/')
        message = json.loads(res.data)['message']
        self.assertEqual(message, 'Backend is online.')

    def test_404_exception(self):
        """Check the 404 exception message."""
        res = self.get('does_not_exist')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['message'], 'Page does not exist.')
        self.assertEqual(data['result'], 'error')
