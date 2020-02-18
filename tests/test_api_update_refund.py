#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class UpdateRefundAPITestCase(BaseAPITestCase):

    def test_update_nothing(self):
        """Updating a refund with no data should do nothing."""
        self.insert_default_refunds()
        refund1 = Refund.query.filter_by(id=1).first()
        res = self.put(url='/refunds/1', data={}, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        refund2 = Refund.query.filter_by(id=1).first()
        self.assertEqual(refund1, refund2)

    def test_update_forbidden_field(self):
        """Updating a forbidden field should raise an error."""
        self.insert_default_refunds()
        self.assertEqual(Refund.query.filter_by(id=1).first().id, 1)
        data = {'id': 2}
        res = self.put(url='/refunds/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)
        self.assertEqual(Refund.query.filter_by(id=1).first().id, 1)

    def test_update_non_existing_refund(self):
        """Updating a non existing refund should raise an error."""
        self.insert_default_refunds()
        data = {'revoked': True}
        res = self.put(url='/refunds/6', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_update_revoke_refund_twice(self):
        """Revoking a refund twice should raise an error and do nothing."""
        self.insert_default_refunds()
        data = {'revoked': True}
        res = self.put(url='/refunds/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        self.assertTrue(Refund.query.filter_by(id=1).first().revoked)
        res = self.put(url='/refunds/1', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        self.assertTrue(Refund.query.filter_by(id=1).first().revoked)

    def test_update_wrong_type(self):
        """A wrong field type should raise an error."""
        self.insert_default_refunds()
        refund1 = Refund.query.filter_by(id=1).first()
        data = {'revoked': "True"}
        res = self.put(url='/refunds/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        refund2 = Refund.query.filter_by(id=1).first()
        self.assertEqual(refund1, refund2)

    def test_update_unknown_field(self):
        """An unknown field should raise an error."""
        self.insert_default_refunds()
        data = {'color': 'red'}
        res = self.put(url='/refunds/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_refund_revoked(self):
        """Update refund revoked field."""
        self.insert_default_refunds()
        self.assertFalse(Refund.query.filter_by(id=1).first().revoked)
        data = {'revoked': True}
        res = self.put(url='/refunds/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Updated refund')
        self.assertTrue(Refund.query.filter_by(id=1).first().revoked)
