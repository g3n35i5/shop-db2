#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from flask import json

import shopdb.exceptions as exc
from shopdb.api import db
from shopdb.models import *
from tests.base_api import BaseAPITestCase


class CreateReplenishmentCollectionsAPITestCase(BaseAPITestCase):

    def test_create_replenishment_collection_as_admin(self):
        """Creating a ReplenishmentCollection as admin"""
        self.insert_default_replenishmentcollections()
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]

        data = {
            'replenishments': replenishments,
            'comment': 'My test comment',
            'timestamp': '2020-02-24 12:00:00Z',
            'seller_id': 5
        }
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertTrue('message' in data)
        self.assertEqual(data['message'], 'Created replenishmentcollection.')

        replcoll = ReplenishmentCollection.query.filter_by(id=3).first()
        self.assertEqual(replcoll.id, 3)
        self.assertEqual(replcoll.admin_id, 1)
        self.assertEqual(replcoll.comment, 'My test comment')
        self.assertEqual(replcoll.price, 220)
        self.assertEqual(str(replcoll.timestamp), '2020-02-24 12:00:00')
        self.assertFalse(replcoll.revoked)
        self.assertEqual(replcoll.revokehistory, [])
        repls = replcoll.replenishments.all()
        for i, dict in enumerate(replenishments):
            for key in dict:
                self.assertEqual(getattr(repls[i], key), dict[key])

    def test_check_users_credit_after_inserting_replenishmentcollection(self):
        """The credit of the user who is referred by the 'seller_id' should change after a replenishmentcollection"""
        self.insert_default_replenishmentcollections()
        collections = ReplenishmentCollection.query.all()
        sum_collections = 0
        for collection in collections:
            self.assertEqual(collection.seller_id, 5)
            sum_collections += collection.price

        seller = User.query.filter(User.id == 5).first()
        self.assertEqual(sum_collections, seller.credit)

        # Revoke the first collection. The user's credit should decrease by the price of the collection
        collection = ReplenishmentCollection.query.filter_by(id=1).first()
        collection.set_revoked(revoked=True, admin_id=1)
        price = collection.price
        db.session.commit()
        seller = User.query.filter(User.id == 5).first()
        self.assertEqual(sum_collections - price, seller.credit)

    def test_create_replenishmentcollection_reactivate_product(self):
        """
        If a product was marked as inactive with a stocktaking, it can
        be set to active again with a replenishment. This functionality is
        checked with this test.
        """
        # Mark product 1 as inactive
        Product.query.filter_by(id=1).first().active = False
        db.session.commit()
        self.assertFalse(Product.query.filter_by(id=1).first().active)
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {
            'replenishments': replenishments,
            'comment': 'My test comment',
            'timestamp': '2020-02-24 12:00:00Z',
            'seller_id': 5
        }
        self.post(url='/replenishmentcollections', data=data, role='admin')
        self.assertTrue(Product.query.filter_by(id=1).first().active)

    def test_create_replenishmentcollection_as_user(self):
        """Creating a ReplenishmentCollection as user"""
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {
            'replenishments': replenishments,
            'comment': 'My test comment',
            'timestamp': '2020-02-24 12:00:00Z',
            'seller_id': 5
        }
        res = self.post(url='/replenishmentcollections', data=data,
                        role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_create_replenishmentcollection_with_missing_data_I(self):
        """Creating a ReplenishmentCollection with missing data"""
        res = self.post(url='/replenishmentcollections', data={},
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_replenishmentcollection_with_missing_data_II(self):
        """Creating a ReplenishmentCollection with missing data for repl"""
        replenishments = [{'product_id': 1, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {
            'replenishments': replenishments,
            'comment': 'My test comment',
            'timestamp': '2020-02-24 12:00:00Z',
            'seller_id': 5
        }
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_replenishmentcollection_with_missing_data_III(self):
        """Creating a ReplenishmentCollection with empty repl"""
        data = {
            'replenishments': [],
            'comment': 'My test comment',
            'timestamp': '2020-02-24 12:00:00Z',
            'seller_id': 5
        }
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_replenishmentcollection_with_missing_data_IV(self):
        """Creating a ReplenishmentCollection with missing timestamp"""
        data = {
            'replenishments': [{'product_id': 2, 'amount': 20, 'total_price': 20}],
            'comment': 'My test comment',
            'seller_id': 5
        }
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_replenishmentcollection_with_missing_data_V(self):
        """Creating a ReplenishmentCollection with missing seller_id"""
        data = {
            'replenishments': [{'product_id': 2, 'amount': 20, 'total_price': 20}],
            'comment': 'My test comment', 'timestamp': '2020-02-24 12:00:00Z'
        }
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_replenishmentcollection_with_unknown_field_I(self):
        """
        Creating a replenishmentcollection with unknown field in the
        collection itself should raise an exception.
        """
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {'replenishments': replenishments,
                'Nonsense': 9,
                'comment': 'My test comment',
                'timestamp': '2020-02-24 12:00:00Z',
                'seller_id': 5
                }
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_create_replenishmentcollection_with_unknown_field_II(self):
        """
        Creating a replenishmentcollection with unknown field in one of the
        replenishments should raise an exception.
        """
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'Nonsense': 98,
                           'total_price': 20}]
        data = {
            'replenishments': replenishments,
            'comment': 'My test comment',
            'timestamp': '2020-02-24 12:00:00Z',
            'seller_id': 5
        }
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_create_replenishmentcollection_with_wrong_type_I(self):
        """
        Creating a replenishmentcollection with wrong type in the
        replenishmentcollection itself should raise an exception.
        """
        replenishments = [{'product_id': 1, 'amount': 'Hallo',
                           'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {
            'replenishments': replenishments,
            'comment': 'My test comment',
            'timestamp': '2020-02-24 12:00:00Z',
            'seller_id': 5
        }
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_create_replenishmentcollection_with_wrong_type_II(self):
        """
        Creating a replenishmentcollection with wrong type in one of the
        replenishments should raise an exception.
        """
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': '2', 'amount': 20, 'total_price': 20}]
        data = {
            'replenishments': replenishments,
            'comment': 'My test comment',
            'timestamp': '2020-02-24 12:00:00Z',
            'seller_id': 5
        }
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_create_replenishmentcollection_with_invalid_amount(self):
        """Creating a replenishmentcollection with negative amount"""
        replenishments = [{'product_id': 1, 'amount': -10, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {
            'replenishments': replenishments,
            'comment': 'My test comment',
            'timestamp': '2020-02-24 12:00:00Z',
            'seller_id': 5
        }
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidAmount)

    def test_create_replenishmentcollection_with_non_existing_product(self):
        """Creating a replenishmentcollection with a non existing product_id"""
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 20, 'amount': 20, 'total_price': 20}]
        data = {
            'replenishments': replenishments,
            'comment': 'My test comment',
            'timestamp': '2020-02-24 12:00:00Z',
            'seller_id': 5
        }
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_create_replenishmentcollection_with_non_existing_seller(self):
        """Creating a replenishmentcollection with a non existing product_id"""
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {
            'replenishments': replenishments,
            'comment': 'My test comment',
            'timestamp': '2020-02-24 12:00:00Z',
            'seller_id': 6
        }
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)
