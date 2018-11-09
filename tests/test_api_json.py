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
import datetime


class JSONAPITestCase(BaseAPITestCase):
    def test_empty_json(self):
        """An empty json body should raise an error."""
        res = self.client.post('/login', data=None)
        self.assertException(res, exc.InvalidJSON)
