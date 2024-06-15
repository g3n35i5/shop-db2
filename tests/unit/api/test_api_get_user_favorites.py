#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

import shop_db2.exceptions as exc
from shop_db2.api import db
from shop_db2.models import Product, Purchase, User
from tests.base_api import BaseAPITestCase


class GetUserFavoritesAPITestCase(BaseAPITestCase):
    @staticmethod
    def _insert_purchases() -> None:
        """Helper function to insert some test purchases."""
        # Insert user 1 purchases.
        p1 = Purchase(user_id=1, product_id=1, amount=4)
        p2 = Purchase(user_id=1, product_id=2, amount=4)
        p3 = Purchase(user_id=1, product_id=3, amount=5)
        p4 = Purchase(user_id=1, product_id=4, amount=1)
        p5 = Purchase(user_id=1, product_id=3, amount=5)
        p6 = Purchase(user_id=1, product_id=2, amount=4)

        # Insert other users purchases.
        p7 = Purchase(user_id=2, product_id=4, amount=30)
        p8 = Purchase(user_id=3, product_id=3, amount=4)
        p9 = Purchase(user_id=3, product_id=1, amount=12)
        p10 = Purchase(user_id=2, product_id=2, amount=8)
        for p in [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10]:
            db.session.add(p)
        db.session.commit()

    def test_get_user_favorites(self) -> None:
        """This test ensures that the user's favorites are generated reliably."""
        self._insert_purchases()
        res = self.get(url="/users/1/favorites")
        favorites = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(favorites, [3, 2, 1, 4])

    def test_get_user_favorites_inactive_product(self) -> None:
        """This test ensures that inactive products are not included in the
        favorites.
        """
        self._insert_purchases()
        # Mark product with id 1 as inactive
        Product.query.filter_by(id=1).first().active = False
        db.session.commit()

        # Get the favorites
        res = self.get(url="/users/1/favorites")
        favorites = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(favorites, [3, 2, 4])

    def test_get_user_favorites_no_purchase(self) -> None:
        """This test ensures that an empty list is displayed for the user's
        favorites if no purchases have yet been made.
        """
        res = self.get(url="/users/1/favorites")
        favorites = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(favorites, [])

    def test_get_user_favorites_non_existing_user(self) -> None:
        """Getting the favorites from a non existing user should raise an error."""
        res = self.get(url="/users/6/favorites")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_get_user_favorites_non_verified_user(self) -> None:
        """Getting the favorites from a non verified user should raise an error."""
        res = self.get(url="/users/4/favorites")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsNotVerified)

    def test_get_user_favorites_inactive_user(self) -> None:
        """Getting the favorites from an inactive user should raise an error."""
        User.query.filter_by(id=3).first().set_rank_id(4, 1)
        db.session.commit()
        res = self.get(url="/users/3/favorites")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsInactive)
