from shopdb.api import *
import shopdb.models as models
import shopdb.exceptions as exc
from sqlalchemy.exc import *
from time import sleep
from base import u_emails, u_passwords, u_firstnames, u_lastnames, u_usernames
from base_api import BaseAPITestCase
from flask import json
import jwt
from copy import copy
import pdb


class GetConfigurationAPITestCase(BaseAPITestCase):
    def test_get_configuration(self):
        """TODO"""
        res = self.get(url='/configuration')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'configuration' in data
        assert 'DEBT_LIMIT' in data['configuration']
        self.assertEqual(data['configuration']['DEBT_LIMIT'], -2000)
