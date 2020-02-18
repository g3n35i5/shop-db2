#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class UpdateStocktakingAPITestCase(BaseAPITestCase):

    def test_update_stocktaking_as_admin(self):
        """Updating count of a single stocktaking"""
        self.insert_default_stocktakingcollections()
        data = {'count': 20}
        res = self.put(url='/stocktakings/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message', 'updated_fields' in data
        self.assertEqual(data['message'], 'Updated stocktaking')
        self.assertEqual(data['updated_fields'], ['count'])
        stocktaking = Stocktaking.query.filter_by(id=1).first()
        self.assertEqual(stocktaking.count, 20)

    def test_update_stocktaking_no_changes(self):
        """Updating a single stocktaking with same count"""
        self.insert_default_stocktakingcollections()
        data = {'count': 100}
        res = self.put(url='/stocktakings/1', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_update_stocktaking_as_user(self):
        """Updating a single stocktaking as user"""
        self.insert_default_stocktakingcollections()
        data = {'count': 0}
        res = self.put(url='/stocktakings/1', data=data, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_update_stocktaking_with_invalid_id(self):
        """Updating a single stocktaking that does not exist"""
        self.insert_default_stocktakingcollections()
        data = {'count': 10}
        res = self.put(url='/stocktakings/20', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_update_stocktaking_with_invalid_amount(self):
        """Updating a single stocktaking with an invalid amount"""
        self.insert_default_stocktakingcollections()
        data = {'count': -2}
        res = self.put(url='/stocktakings/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidAmount)

    def test_update_stocktaking_with_forbidden_field(self):
        """Updating a forbidden field of a single stocktaking"""
        self.insert_default_stocktakingcollections()
        data = {'product_id': 4}
        res = self.put(url='/stocktakings/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)

    def test_update_stocktaking_with_unknown_field(self):
        """Updating a unknown field of a single stocktaking"""
        self.insert_default_stocktakingcollections()
        data = {'amount': 0}
        res = self.put(url='/stocktakings/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_stocktaking_with_wrong_type(self):
        """Updating a field of a single stocktaking with a wrong type"""
        self.insert_default_stocktakingcollections()
        data = {'count': '2'}
        res = self.put(url='/stocktakings/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
