#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

import shop_db2.exceptions as exc
from shop_db2.api import db
from shop_db2.models import Purchase
from tests.base_api import BaseAPITestCase


class ListPurchasesAPITestCase(BaseAPITestCase):
    def test_list_purchases_as_admin(self) -> None:
        """Test for listing all purchases as admin"""
        # Do 5 purchases
        self.insert_default_purchases()
        res = self.get(url="/purchases", role="admin")
        self.assertEqual(res.status_code, 200)
        purchases = json.loads(res.data)
        self.assertEqual(len(purchases), 5)
        self.assertEqual(purchases[0]["user_id"], 1)
        self.assertEqual(purchases[1]["user_id"], 2)
        self.assertEqual(purchases[2]["user_id"], 2)
        self.assertEqual(purchases[3]["user_id"], 3)
        self.assertEqual(purchases[4]["user_id"], 1)

        required = [
            "id",
            "timestamp",
            "user_id",
            "product_id",
            "productprice",
            "amount",
            "revoked",
        ]
        for purchase in purchases:
            assert all(x in purchase for x in required)

    def test_list_purchases_as_user(self) -> None:
        """Test for listing all purchases without token. Revoked purchases
        should not be listed.
        """
        # Do 5 purchases
        self.insert_default_purchases()
        # Revoke the third purchase
        purchase = Purchase.query.filter_by(id=3).first()
        purchase.set_revoked(revoked=True)
        db.session.commit()
        res = self.get(url="/purchases")
        self.assertEqual(res.status_code, 200)
        purchases = json.loads(res.data)
        self.assertEqual(len(purchases), 4)
        self.assertEqual(purchases[0]["user_id"], 1)
        self.assertEqual(purchases[1]["user_id"], 2)
        self.assertEqual(purchases[2]["user_id"], 3)
        self.assertEqual(purchases[3]["user_id"], 1)

        required = ["id", "timestamp", "user_id", "product_id", "amount"]
        forbidden = ["productprice", "revoked"]
        for purchase in purchases:
            assert all(x in purchase for x in required)
            assert all(x not in purchase for x in forbidden)

    def test_list_purchases_with_limit(self) -> None:
        """Listing the purchases with a limit."""
        # Do 5 purchases
        self.insert_default_purchases()

        # Revoke the third purchase
        purchase = Purchase.query.filter_by(id=3).first()
        purchase.set_revoked(revoked=True)
        db.session.commit()
        res = self.get(
            url="/purchases",
            params={
                "sort": {"field": "id", "order": "DESC"},
                "pagination": {"page": 1, "perPage": 3},
            },
        )
        self.assertEqual(res.status_code, 200)
        purchases = json.loads(res.data)
        self.assertEqual(len(purchases), 3)
        self.assertEqual(purchases[0]["id"], 5)
        self.assertEqual(purchases[1]["id"], 4)  # <- Third purchase is revoked!
        self.assertEqual(purchases[2]["id"], 2)

    def test_invalid_parameter(self) -> None:
        res = self.get(url="/purchases", params={"unknown": 2})
        self.assertEqual(res.status_code, 400)
        self.assertException(res, exc.InvalidQueryParameters)

    def test_wrong_parameter_type(self) -> None:
        res = self.get(url="/purchases", params={"limit": "two"})
        self.assertEqual(res.status_code, 400)
        self.assertException(res, exc.InvalidQueryParameters)
