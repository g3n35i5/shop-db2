#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

import shop_db2.exceptions as exc
from shop_db2.api import db
from shop_db2.models import Purchase, User, UserVerification
from tests.base import BaseTestCase


class UserModelTestCase(BaseTestCase):
    def test_user_representation(self):
        """Testing the user representation"""
        user = User.query.filter_by(id=1).first()
        self.assertEqual(repr(user), "<User 1: Jones, William>")

    def test_get_user_purchases(self):
        """Testing get user purchase list"""
        user = User.query.filter_by(id=1).first()
        self.assertEqual(len(user.purchases.all()), 0)
        amounts = [1, 5, 6, 8]
        ids = [1, 2, 4, 1]
        for i in range(0, 4):
            p = Purchase(user_id=1, product_id=ids[i], amount=amounts[i])
            db.session.add(p)
        db.session.commit()
        user = User.query.filter_by(id=1).first()
        self.assertEqual(len(user.purchases.all()), 4)
        for i in range(0, 4):
            self.assertEqual(user.purchases.all()[i].amount, amounts[i])
            self.assertEqual(user.purchases.all()[i].product_id, ids[i])

    def test_user_set_password(self):
        """Test the password setter method"""
        user = User.query.filter_by(id=1).first()
        check = self.bcrypt.check_password_hash(user.password, "test_password")
        self.assertFalse(check)
        user.password = self.bcrypt.generate_password_hash("test_password")
        db.session.commit()
        user = User.query.filter_by(id=1).first()
        check = self.bcrypt.check_password_hash(user.password, "test_password")
        self.assertTrue(check)

    def test_verify_user_twice(self):
        """Users cant be verified twice"""
        user = User.query.filter_by(id=1).first()
        self.assertTrue(user.is_verified)
        with self.assertRaises(exc.UserAlreadyVerified):
            user.verify(admin_id=1, rank_id=1)

        user = User.query.filter_by(id=1).first()
        self.assertTrue(user.is_verified)

    def test_verify_user(self):
        """Verify a user. We take the last one in the list since all other
        users have already been verified.
        """
        user = User.query.filter_by(id=4).first()
        self.assertFalse(user.is_verified)
        user.verify(admin_id=1, rank_id=1)
        db.session.commit()
        user = User.query.filter_by(id=4).first()
        self.assertTrue(user.is_verified)
        verification = UserVerification.query.order_by(UserVerification.id.desc()).first()
        self.assertEqual(verification.user_id, user.id)
        self.assertEqual(verification.admin_id, 1)

    def test_set_user_rank_id(self):
        """Update the user rank id"""
        user = User.query.filter_by(id=1).first()
        self.assertEqual(user.rank_id, 2)
        self.assertEqual(user.rank.name, "Member")
        user.set_rank_id(rank_id=3, admin_id=1)
        db.session.commit()
        user = User.query.filter_by(id=1).first()
        self.assertEqual(user.rank_id, 3)
        self.assertEqual(user.rank.name, "Alumni")

    def test_update_user_firstname(self):
        """Update the firstname of a user"""
        user = User.query.filter_by(id=1).first()
        self.assertEqual(user.id, 1)
        user.firstname = "Updated_Firstname"
        db.session.commit()
        user = User.query.filter_by(id=1).first()
        self.assertEqual(user.firstname, "Updated_Firstname")

    def test_update_user_lastname(self):
        """Update the lastname of a user"""
        user = User.query.filter_by(id=1).first()
        self.assertEqual(user.id, 1)
        user.lastname = "Updated_Lastname"
        db.session.commit()
        user = User.query.filter_by(id=1).first()
        self.assertEqual(user.lastname, "Updated_Lastname")

    def test_insert_purchase_as_non_verified_user(self):
        """It must be ensured that non-verified users cannot make purchases."""
        user = User.query.filter_by(id=4).first()
        self.assertFalse(user.is_verified)
        with self.assertRaises(exc.UserIsNotVerified):
            Purchase(user_id=4, product_id=1)
        db.session.rollback()
        # No purchase may have been made at this point
        purchases = Purchase.query.all()
        self.assertEqual(len(purchases), 0)

    def test_get_favorite_product_ids(self):
        """This test ensures that the ids of purchased products are returned in
        descending order with respect to the frequency with which they were
        purchased by the user.
        """
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

        favorites = User.query.filter_by(id=1).first().favorites
        self.assertEqual([3, 2, 1, 4], favorites)

    def test_get_favorite_product_ids_without_purchases(self):
        """This test ensures that an empty list for the favorite products is
        returned if no purchases have been made by the user yet.
        """
        favorites = User.query.filter_by(id=1).first().favorites
        self.assertEqual([], favorites)
