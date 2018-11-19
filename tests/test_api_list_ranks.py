from tests.base_api import BaseAPITestCase
from tests.base import r_names, r_limits
from flask import json


class ListRanksAPITestCase(BaseAPITestCase):
    def test_list_ranks(self):
        """Test listing all ranks."""
        res = self.get(url='/ranks')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'ranks' in data
        ranks = data['ranks']
        self.assertEqual(len(ranks), 3)
        for i in range(3):
            self.assertEqual(ranks[i]['name'], r_names[i])
            self.assertEqual(ranks[i]['debt_limit'], r_limits[i])
