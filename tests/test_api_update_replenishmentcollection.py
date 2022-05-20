#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

import datetime

from flask import json

import shopdb.exceptions as exc
from shopdb.models import ReplenishmentCollection
from tests.base_api import BaseAPITestCase


class UpdateReplenishmentCollectionsAPITestCase(BaseAPITestCase):
    def test_revoke_replenishmentcollection(self):
        """Revoke a replenishmentcollection"""
        self.insert_default_replenishmentcollections()
        res = self.put(
            url="/replenishmentcollections/1", data={"revoked": True}, role="admin"
        )
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertTrue("message" in data)
        self.assertEqual(data["message"], "Updated replenishmentcollection")
        replcoll = ReplenishmentCollection.query.filter_by(id=1).first()
        self.assertEqual(replcoll.revoked, True)
        required = ["id", "revoked", "timestamp"]
        for item in required:
            assert item in replcoll.revokehistory[0]

    def test_revoke_replenishmentcollection_multiple_times(self):
        """Revoke a replenishmentcollection multiple times"""
        self.insert_default_replenishmentcollections()
        res = self.put(
            url="/replenishmentcollections/1", data={"revoked": True}, role="admin"
        )
        self.assertEqual(res.status_code, 201)
        res = self.put(
            url="/replenishmentcollections/1", data={"revoked": False}, role="admin"
        )
        self.assertEqual(res.status_code, 201)
        res = self.put(
            url="/replenishmentcollections/1", data={"revoked": True}, role="admin"
        )
        self.assertEqual(res.status_code, 201)
        replcoll = ReplenishmentCollection.query.filter_by(id=1).first()
        self.assertEqual(replcoll.revoked, True)
        self.assertEqual(len(replcoll.revokehistory), 3)
        required = ["id", "revoked", "timestamp"]
        for i in replcoll.revokehistory:
            for item in required:
                assert item in i

    def test_update_replenishmentcollection_comment(self):
        """Update the comment of a replenishmentcollection"""
        self.insert_default_replenishmentcollections()
        res = self.put(
            url="/replenishmentcollections/1", data={"comment": "FooBar"}, role="admin"
        )
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertTrue("message" in data)
        self.assertEqual(data["message"], "Updated replenishmentcollection")
        replcoll = ReplenishmentCollection.query.filter_by(id=1).first()
        self.assertEqual(replcoll.comment, "FooBar")

    def test_update_replenishmentcollection_timestamp(self):
        """Update the timestamp of a replenishmentcollection"""
        self.insert_default_replenishmentcollections()
        timestamp = "2015-01-01 01:01:01Z"
        res = self.put(
            url="/replenishmentcollections/1",
            data={"timestamp": timestamp},
            role="admin",
        )
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertTrue("message" in data)
        self.assertEqual(data["message"], "Updated replenishmentcollection")
        replcoll = ReplenishmentCollection.query.filter_by(id=1).first()
        self.assertEqual(str(replcoll.timestamp), "2015-01-01 01:01:01")

    def test_update_replenishmentcollection_invalid_timestamp(self):
        """Update the timestamp of a replenishmentcollection with a timestamp in the future must fail"""
        self.insert_default_replenishmentcollections()
        old_timestamp = ReplenishmentCollection.query.filter_by(id=1).first().timestamp
        timestamp = (datetime.datetime.now() + datetime.timedelta(days=2)).timestamp()
        res = self.put(
            url="/replenishmentcollections/1",
            data={"timestamp": int(timestamp)},
            role="admin",
        )
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        replcoll = ReplenishmentCollection.query.filter_by(id=1).first()
        self.assertEqual(replcoll.timestamp, old_timestamp)

    def test_revoke_replenishmentcollection_as_user(self):
        """Revoking a replenishmentcollection as user should be forbidden"""
        res = self.put(
            url="/replenishmentcollections/1", data={"revoked": True}, role="user"
        )
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_update_replenishmentcollection_no_changes(self):
        """Revoking a replenishmentcollection with no changes"""
        self.insert_default_replenishmentcollections()
        res = self.put(
            url="/replenishmentcollections/1", data={"revoked": False}, role="admin"
        )
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_update_non_existing_replenishmentcollection(self):
        """Revoking a replenishmentcollection that doesnt exist"""
        self.insert_default_replenishmentcollections()
        res = self.put(
            url="/replenishmentcollections/4", data={"revoked": True}, role="admin"
        )
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_update_replenishmentcollection_forbidden_field(self):
        """Updating forbidden fields of a replenishmentcollection"""
        self.insert_default_replenishmentcollections()
        res = self.put(
            url="/replenishmentcollections/1",
            data={"revoked": True, "admin_id": "1"},
            role="admin",
        )
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)

    def test_update_replenishmentcollection_unknown_field(self):
        """Update non existing fields of a replenishmentcollection"""
        self.insert_default_replenishmentcollections()
        res = self.put(
            url="/replenishmentcollections/1", data={"Nonsense": ""}, role="admin"
        )
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_replenishmentcollection_wrong_type(self):
        """Update fields of a replenishmentcollection with wrong types"""
        self.insert_default_replenishmentcollections()
        res = self.put(
            url="/replenishmentcollections/1", data={"revoked": "yes"}, role="admin"
        )
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_update_replenishmentcollection_with_no_data(self):
        """Update a replenishmentcollection with no data"""
        self.insert_default_replenishmentcollections()
        res = self.put(url="/replenishmentcollections/1", data={}, role="admin")
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_update_replenishmentcollection_revoke_error(self):
        """Trying to rerevoke a replenishmentcollection which only has revoked
        replenishments should raise an error"""
        self.insert_default_replenishmentcollections()
        # revoke the corresponding replenishments
        res = self.put(url="/replenishments/1", data={"revoked": True}, role="admin")
        self.assertEqual(res.status_code, 201)
        res = self.put(url="/replenishments/2", data={"revoked": True}, role="admin")
        self.assertEqual(res.status_code, 201)
        # actual test
        res = self.put(
            url="/replenishmentcollections/1", data={"revoked": False}, role="admin"
        )
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotRevocable)
