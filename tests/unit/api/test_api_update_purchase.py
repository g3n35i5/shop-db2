#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

import shop_db2.exceptions as exc
from shop_db2.api import db
from shop_db2.models import Product, Purchase
from tests.base_api import BaseAPITestCase


class UpdatePurchaseAPITestCase(BaseAPITestCase):
    def test_update_nothing(self) -> None:
        """Updating a purchase with no data should do nothing."""
        self.insert_default_purchases()
        purchase1 = Purchase.query.filter_by(id=1).first()
        res = self.put(url="/purchases/1", data={}, role="admin")
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        purchase2 = Purchase.query.filter_by(id=1).first()
        self.assertEqual(purchase1, purchase2)

    def test_update_forbidden_field(self) -> None:
        """Updating a forbidden field should raise an error."""
        self.insert_default_purchases()
        self.assertEqual(Purchase.query.filter_by(id=1).first().id, 1)
        data = {"id": 2}
        res = self.put(url="/purchases/1", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)
        self.assertEqual(Purchase.query.filter_by(id=1).first().id, 1)

    def test_update_non_existing_purchase(self) -> None:
        """Updating a non existing purchase should raise an error."""
        self.insert_default_purchases()
        data = {"amount": 5}
        res = self.put(url="/purchases/6", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_revoke_purchase_made_by_admin(self) -> None:
        """Purchase, which have been inserted from administrators can only
        be revoked by an administrator.
        """
        # Create purchase with admin privileges
        data = {"user_id": 2, "product_id": 1, "amount": 1}
        self.post(url="/purchases", data=data, role="admin")
        purchase = Purchase.query.order_by(Purchase.id.desc()).first()
        self.assertTrue(purchase.admin_id is not None)
        self.assertEqual(1, purchase.amount)
        self.assertFalse(purchase.revoked)

        # Users are not allowed to revoke (or even update) this purchase
        for role in [None, "user"]:
            res = self.put(url=f"/purchases/{purchase.id}", data={"revoked": True}, role=role)
            self.assertException(res, exc.EntryNotRevocable)
            purchase = Purchase.query.order_by(Purchase.id.desc()).first()
            self.assertFalse(purchase.revoked)

        # Administrators are allowed to update this purchase
        res = self.put(
            url=f"/purchases/{purchase.id}",
            data={"revoked": True, "amount": 2},
            role="admin",
        )
        self.assertEqual(res.status_code, 201)
        purchase = Purchase.query.order_by(Purchase.id.desc()).first()
        self.assertTrue(purchase.revoked)
        self.assertEqual(2, purchase.amount)

    def test_update_revoke_purchase_twice(self) -> None:
        """Revoking a purchase twice should raise an error and do nothing."""
        self.insert_default_purchases()
        data = {"revoked": True}
        res = self.put(url="/purchases/1", data=data, role="admin")
        self.assertEqual(res.status_code, 201)
        self.assertTrue(Purchase.query.filter_by(id=1).first().revoked)
        res = self.put(url="/purchases/1", data=data, role="admin")
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        self.assertTrue(Purchase.query.filter_by(id=1).first().revoked)

    def test_update_wrong_type(self) -> None:
        """A wrong field type should raise an error."""
        self.insert_default_purchases()
        purchase1 = Purchase.query.filter_by(id=1).first()
        data = {"amount": "2"}
        res = self.put(url="/purchases/1", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        purchase2 = Purchase.query.filter_by(id=1).first()
        self.assertEqual(purchase1, purchase2)

    def test_update_unknown_field(self) -> None:
        """An unknown field should raise an error."""
        self.insert_default_purchases()
        data = {"color": "red"}
        res = self.put(url="/purchases/1", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_purchase_revoked(self) -> None:
        """Update purchase revoked field."""
        self.insert_default_purchases()
        self.assertFalse(Purchase.query.filter_by(id=1).first().revoked)
        data = {"revoked": True}
        res = self.put(url="/purchases/1", data=data, role="admin")
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data["message"], "Updated purchase")
        self.assertEqual(len(data["updated_fields"]), 1)
        self.assertEqual(data["updated_fields"][0], "revoked")
        self.assertTrue(Purchase.query.filter_by(id=1).first().revoked)

    def test_update_non_revocable_purchase_revoke(self) -> None:
        """In case that the product is not revocable, an exception must be made."""
        # Make sure, that product 1 is not revocable.
        product = Product.query.filter_by(id=1).first()
        product.revocable = False
        db.session.commit()

        self.insert_default_purchases()
        self.assertFalse(Purchase.query.filter_by(id=1).first().revoked)
        data = {"revoked": True}
        res = self.put(url="/purchases/1", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotRevocable)
        self.assertFalse(Purchase.query.filter_by(id=1).first().revoked)

    def test_update_purchase_amount(self) -> None:
        """Update product price"""
        self.insert_default_purchases()
        purchase = Purchase.query.filter_by(id=1).first()
        self.assertEqual(purchase.amount, 1)
        self.assertEqual(purchase.price, 300)
        data = {"amount": 10}
        res = self.put(url="/purchases/1", data=data, role="admin")
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data["message"], "Updated purchase")
        self.assertEqual(len(data["updated_fields"]), 1)
        self.assertEqual(data["updated_fields"][0], "amount")
        purchase = Purchase.query.filter_by(id=1).first()
        self.assertEqual(purchase.amount, 10)
        self.assertEqual(purchase.price, 3000)
