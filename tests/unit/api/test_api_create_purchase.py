#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from copy import copy
from typing import Any, Dict

from flask import json

import shop_db2.exceptions as exc
from shop_db2.api import db
from shop_db2.models import Product, Purchase, Rank, Tag, User
from tests.base_api import BaseAPITestCase


class CreatePurchaseAPITestCase(BaseAPITestCase):
    def test_create_purchase(self) -> None:
        """Create a purchase."""
        data = {"user_id": 2, "product_id": 3, "amount": 4}
        res = self.post(url="/purchases", data=data)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue("message" in data)
        self.assertEqual(data["message"], "Purchase created.")
        purchases = Purchase.query.all()
        self.assertEqual(len(purchases), 1)
        self.assertEqual(purchases[0].user_id, 2)
        self.assertEqual(purchases[0].product_id, 3)
        self.assertEqual(purchases[0].amount, 4)
        self.assertEqual(purchases[0].productprice, 100)
        self.assertEqual(purchases[0].price, 400)
        self.assertFalse(purchases[0].revoked)
        print()

    def test_create_purchase_insufficient_credit_alumni(self) -> None:
        """Create a purchase with not enough credit."""
        data = {"user_id": 2, "product_id": 3, "amount": 21}
        self.assertEqual(User.query.filter_by(id=2).first().rank_id, 3)

        res = self.post(url="/purchases", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InsufficientCredit)

    def test_create_purchase_insufficient_credit_contender(self) -> None:
        """Create a purchase with not enough credit."""
        data = {"user_id": 3, "product_id": 3, "amount": 4}
        self.assertEqual(User.query.filter_by(id=3).first().rank_id, 1)

        res = self.post(url="/purchases", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InsufficientCredit)

    def test_create_purchase_insufficient_credit_by_admin(self) -> None:
        """If the purchase is made by an administrator, the credit limit
        may be exceeded.
        """
        data = {"user_id": 3, "product_id": 3, "amount": 4}
        self.assertEqual(User.query.filter_by(id=3).first().rank_id, 1)

        res = self.post(url="/purchases", data=data, role="admin")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue("message" in data)
        self.assertEqual(data["message"], "Purchase created.")

    def test_create_purchase_wrong_type(self) -> None:
        """Create a purchase with wrong type(s)."""
        data = {"user_id": 2, "product_id": 3, "amount": 4}

        for field in data:
            copy_data = copy(data)
            copy_data[field] = 100.0  # type: ignore
            res = self.post(url="/purchases", data=copy_data)
            self.assertEqual(res.status_code, 401)
            self.assertException(res, exc.WrongType)

        self.assertEqual(len(Purchase.query.all()), 0)

    def test_create_purchase_with_system_user(self) -> None:
        """Creating purchases with a system user is only allowed for administrators"""
        # Add system user rank
        db.session.add(Rank(name="System", is_system_user=True))
        db.session.commit()
        rank = db.session.query(Rank).filter(Rank.is_system_user.is_(True)).first()
        user = User.query.filter_by(id=2).first()
        user.set_rank_id(rank_id=rank.id, admin_id=1)
        db.session.commit()

        data = {"user_id": 2, "product_id": 1, "amount": 2}

        for role in [None, "user"]:
            res = self.post(url="/purchases", role=role, data=data)
            self.assertException(res, exc.UnauthorizedAccess)

        res = self.post(url="/purchases", role="admin", data=data)
        data = json.loads(res.data)
        self.assertTrue("message" in data)
        self.assertEqual(data["message"], "Purchase created.")
        purchases = Purchase.query.all()
        self.assertEqual(len(purchases), 1)

    def test_create_multiple_purchases_at_once(self) -> None:
        """Creating multiple purchases at once"""
        data = [
            {"user_id": 2, "product_id": 1, "amount": 1},
            {"user_id": 2, "product_id": 2, "amount": 1},
            {"user_id": 2, "product_id": 3, "amount": 1},
        ]
        res = self.post(url="/purchases", data=data)
        response_data: Dict[str, Any] = json.loads(res.data)
        self.assertEqual(response_data["message"], "Purchase created.")
        purchases = Purchase.query.all()
        self.assertEqual(3, len(purchases))

    def test_create_multiple_purchases_with_invalid_data(self) -> None:
        """This test ensures that if you create multiple purchases at once, a single error will
        prevent the whole transaction
        """
        data = [
            {"user_id": 2, "product_id": 1, "amount": 1},
            {"user_id": 2, "product_id": 2, "amount": 1},
            {"user_id": 2, "product_id": 3, "amount": "1"},
        ]
        res = self.post(url="/purchases", data=data)
        self.assertException(res, exc.WrongType)
        purchases = Purchase.query.all()
        self.assertEqual(0, len(purchases))

    def test_create_purchase_with_timestamp_as_admin(self) -> None:
        """Creating a purchase with a timestamp as administrator"""
        data = {
            "user_id": 2,
            "product_id": 3,
            "amount": 4,
            "timestamp": "2000-01-01 12:00:00 UTC",
        }
        self.post(url="/purchases", role="admin", data=data)
        purchases = Purchase.query.all()
        self.assertEqual(len(purchases), 1)
        self.assertEqual(2000, purchases[0].timestamp.year)

    def test_create_purchase_with_timestamp_without_admin_permissions(self) -> None:
        """Creating a purchase with a timestamp is only allowed for administrators"""
        data = {
            "user_id": 2,
            "product_id": 3,
            "amount": 4,
            "timestamp": "2000-01-01 12:00:00",
        }
        for role in [None, "user"]:
            res = self.post(url="/purchases", role=role, data=data)
            self.assertException(res, exc.ForbiddenField)

    def test_create_purchase_product_not_for_sale(self) -> None:
        """Creating a purchase with a product which is not for sale must raise an exception"""
        # Assign a "not for sale" tag to the product
        tag = db.session.query(Tag).filter(Tag.is_for_sale.is_(False)).first()
        product = Product.query.filter_by(id=1).first()
        product.tags.append(tag)
        db.session.commit()

        data = {"user_id": 1, "product_id": 1, "amount": 2}
        for role in [None, "user"]:
            res = self.post(url="/purchases", role=role, data=data)
            self.assertEqual(res.status_code, 400)
            self.assertException(res, exc.EntryIsNotForSale)
            self.assertEqual(len(Purchase.query.all()), 0)

        self.post(url="/purchases", data=data, role="admin")
        purchases = Purchase.query.all()
        self.assertEqual(1, len(purchases))
        self.assertTrue(purchases[0].admin_id is not None)

    def test_create_purchase_unknown_field(self) -> None:
        """Create a purchase with an unknown field."""
        data = {"user_id": 4, "product_id": 3, "amount": 4, "foo": "bar"}
        res = self.post(url="/purchases", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)
        self.assertEqual(len(Purchase.query.all()), 0)

    def test_create_purchase_not_all_required_fields(self) -> None:
        """Create a purchase missing a required field"""
        data = {"user_id": 4, "product_id": 3}
        res = self.post(url="/purchases", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        self.assertEqual(len(Purchase.query.all()), 0)

    def test_create_purchase_non_verified_user(self) -> None:
        """Create a purchase as non verified user."""
        data = {"user_id": 4, "product_id": 3, "amount": 4}
        res = self.post(url="/purchases", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsNotVerified)
        self.assertEqual(len(Purchase.query.all()), 0)

    def test_create_purchase_inactive_user(self) -> None:
        """Create a purchase as inactive user."""
        User.query.filter_by(id=3).first().set_rank_id(4, 1)
        db.session.commit()
        data = {"user_id": 3, "product_id": 3, "amount": 4}
        res = self.post(url="/purchases", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsInactive)
        self.assertEqual(len(Purchase.query.all()), 0)

    def test_create_purchase_non_existing_user(self) -> None:
        """Create a purchase as non existing user."""
        data = {"user_id": 6, "product_id": 3, "amount": 4}
        res = self.post(url="/purchases", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)
        self.assertEqual(len(Purchase.query.all()), 0)

    def test_create_purchase_inactive_product(self) -> None:
        """Create a purchase with an inactive product."""
        product = Product.query.filter_by(id=4).first()
        product.active = False
        db.session.commit()
        data = {"user_id": 1, "product_id": 4, "amount": 2}
        res = self.post(url="/purchases", role="user", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryIsInactive)
        self.assertEqual(len(Purchase.query.all()), 0)

    def test_create_purchase_inactive_product_by_admin(self) -> None:
        """If the purchase is made by an administrator, the product is allowed
        to be inactive.
        """
        product = Product.query.filter_by(id=4).first()
        product.active = False
        db.session.commit()
        data = {"user_id": 1, "product_id": 4, "amount": 2}
        res = self.post(url="/purchases", role="admin", data=data)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue("message" in data)
        self.assertEqual(data["message"], "Purchase created.")

    def test_create_purchase_invalid_amount(self) -> None:
        """Create a purchase with an invalid amount."""
        data = {"user_id": 1, "product_id": 1, "amount": -1}
        res = self.post(url="/purchases", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidAmount)
        self.assertEqual(len(Purchase.query.all()), 0)

    def test_create_purchase_non_existing_product(self) -> None:
        """Create a purchase with a non existing product."""
        data = {"user_id": 1, "product_id": 5, "amount": 1}
        res = self.post(url="/purchases", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)
        self.assertEqual(len(Purchase.query.all()), 0)
