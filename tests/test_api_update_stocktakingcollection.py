#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class UpdateStocktakingCollectionsAPITestCase(BaseAPITestCase):

    def test_revoke_stocktakingcollection(self):
        """Revoke a stocktakingcollection"""
        self.insert_default_stocktakingcollections()
        res = self.put(url='/stocktakingcollections/1',
                       data={'revoked': True}, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertTrue('message' in data)
        self.assertEqual(data['message'], 'Updated stocktakingcollection')
        collection = StocktakingCollection.query.filter_by(id=1).first()
        self.assertEqual(collection.revoked, True)
        required = ['id', 'revoked', 'timestamp']
        for item in required:
            assert item in collection.revokehistory[0]

    def test_revoke_stocktakingcollection_multiple_times(self):
        """Revoke a stocktakingcollection multiple times"""
        self.insert_default_stocktakingcollections()
        res = self.put(url='/stocktakingcollections/1',
                       data={'revoked': True}, role='admin')
        self.assertEqual(res.status_code, 201)
        res = self.put(url='/stocktakingcollections/1',
                       data={'revoked': False}, role='admin')
        self.assertEqual(res.status_code, 201)
        res = self.put(url='/stocktakingcollections/1',
                       data={'revoked': True}, role='admin')
        self.assertEqual(res.status_code, 201)
        collection = StocktakingCollection.query.filter_by(id=1).first()
        self.assertEqual(collection.revoked, True)
        self.assertEqual(len(collection.revokehistory), 3)
        required = ['id', 'revoked', 'timestamp']
        for i in collection.revokehistory:
            for item in required:
                assert item in i

    def test_revoke_stocktakingcollection_as_user(self):
        """Revoking a stocktakingcollection as user should be forbidden"""
        res = self.put(url='/stocktakingcollections/1',
                       data={'revoked': True}, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_update_stocktakingcollection_no_changes(self):
        """Revoking a stocktakingcollection with no changes"""
        self.insert_default_stocktakingcollections()
        res = self.put(url='/stocktakingcollections/1',
                       data={'revoked': False}, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_update_non_existing_stocktakingcollection(self):
        """Revoking a stocktakingcollection that doesnt exist"""
        self.insert_default_stocktakingcollections()
        res = self.put(url='/stocktakingcollections/4',
                       data={'revoked': True}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_update_stocktakingcollection_forbidden_field(self):
        """Updating forbidden fields of a stocktakingcollection"""
        self.insert_default_stocktakingcollections()
        res = self.put(url='/stocktakingcollections/1',
                       data={'revoked': True, 'timestamp': ''}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)

    def test_update_stocktakingcollection_unknown_field(self):
        """Update non existing fields of a stocktakingcollection"""
        self.insert_default_stocktakingcollections()
        res = self.put(url='/stocktakingcollections/1',
                       data={'Nonsense': ''}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_stocktakingcollection_wrong_type(self):
        """Update fields of a stocktakingcollection with wrong types"""
        self.insert_default_stocktakingcollections()
        res = self.put(url='/stocktakingcollections/1',
                       data={'revoked': 'yes'}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_update_stocktakingcollection_with_no_data(self):
        """Update a stocktakingcollection with no data"""
        self.insert_default_stocktakingcollections()
        res = self.put(url='/stocktakingcollections/1',
                       data={}, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
