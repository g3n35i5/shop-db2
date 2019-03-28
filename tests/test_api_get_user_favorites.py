from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class GetUserFavoritesAPITestCase(BaseAPITestCase):
    def _insert_purchases(self):
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
        
    def test_get_user_favorites(self):
        """
        This test ensures that the user's favorites are generated reliably.
        """
        self._insert_purchases()
        res = self.get(url='/users/1/favorites')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['favorites'], [3, 2, 1, 4])

    def test_get_user_favorites_no_purchase(self):
        """
        This test ensures that an empty list is displayed for the user's
        favorites if no purchases have yet been made.
        """
        res = self.get(url='/users/1/favorites')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['favorites'], [])

    def test_get_user_favorites_non_existing_user(self):
        """
        Getting the favorites from a non existing user should raise an error.
        """
        res = self.get(url='/users/5/favorites')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_get_user_favorites_non_verified_user(self):
        """
        Getting the favorites from a non verified user should raise an error.
        """
        res = self.get(url='/users/4/favorites')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsNotVerified)

    def test_get_user_favorites_inactive_user(self):
        """
        Getting the favorites from an inactive user should raise an error.
        """
        User.query.filter_by(id=3).first().set_rank_id(4, 1)
        db.session.commit()
        res = self.get(url='/users/3/favorites')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsInactive)
