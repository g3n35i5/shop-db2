from tests.base_api import BaseAPITestCase
from flask import json


class ListUsersAPITestCase(BaseAPITestCase):
    def test_list_users_as_user_and_external(self):
        """Get a list of all users as user and as external."""
        for role in ['user', None]:
            res = self.get(url='/users', role=role)
            self.assertEqual(res.status_code, 200)
            data = json.loads(res.data)
            assert 'users' in data
            users = data['users']
            self.assertEqual(len(users), 3)
            for user in users:
                self.assertEqual(len(user), 4)
                for item in ['id', 'firstname', 'lastname', 'rank_id']:
                    assert item in user

    def test_list_users_with_token(self):
        """Get a list of all users as admin. It should contain more information
           than the list which gets returned without a token in the request
           header."""
        res = self.get(url='/users', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'users' in data
        users = data['users']
        self.assertEqual(len(users), 3)
        for user in users:
            self.assertEqual(len(user), 7)
            for item in ['id', 'firstname', 'lastname', 'creation_date',
                         'credit', 'is_admin', 'rank_id']:
                assert item in user
