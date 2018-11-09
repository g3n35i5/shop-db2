from base_api import BaseAPITestCase
from flask import json


class RootAPITestCase(BaseAPITestCase):
    def test_get_api_root(self):
        """An empty json body should raise an error."""
        res = self.client.get('/')
        message = json.loads(res.data)['message']
        self.assertEqual(message, 'Backend is online.')
