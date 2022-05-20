#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

import datetime
from copy import copy

from shopdb.api import db
from shopdb.models import Product, ProductPrice, Purchase, User
from tests.base import BaseTestCase


class PurchaseModelTestCase(BaseTestCase):
    def test_insert_simple_purchase(self):
        """Testing a simple purchase"""
        user = User.query.filter_by(id=1).first()
        self.assertEqual(len(user.purchases.all()), 0)
        self.assertEqual(user.credit, 0)
        product = Product.query.filter_by(id=1).first()
        purchase = Purchase(user_id=user.id, product_id=product.id, amount=1)
        db.session.add(purchase)
        db.session.commit()
        user = User.query.first()
        self.assertEqual(len(user.purchases.all()), 1)
        self.assertEqual(user.credit, -product.price)

    def test_purchase_link_to_its_user(self):
        """
        This test checks whether the reference to the user of a purchase is
        working correctly.
        """
        db.session.add(Purchase(user_id=1, product_id=1, amount=1))
        db.session.commit()
        purchase = Purchase.query.filter_by(id=1).first()
        self.assertEqual(purchase.user, User.query.filter_by(id=1).first())

    def test_insert_multiple_purchases(self):
        """Testing multiple purchases"""
        user = User.query.filter_by(id=1).first()
        self.assertEqual(len(user.purchases.all()), 0)
        self.assertEqual(user.credit, 0)
        purchase_data = [
            {"product_id": 1, "amount": 1},
            {"product_id": 2, "amount": 5},
            {"product_id": 4, "amount": 5},
            {"product_id": 1, "amount": 2},
            {"product_id": 3, "amount": 4},
            {"product_id": 1, "amount": 10},
        ]
        for data in purchase_data:
            purchase = Purchase(user_id=1, **data)
            db.session.add(purchase)
        db.session.commit()

        user = User.query.filter_by(id=1).first()
        self.assertEqual(len(user.purchases.all()), 6)
        for index, data in enumerate(purchase_data):
            self.assertEqual(user.purchases.all()[index].amount, data["amount"])

        c = 0
        for data in purchase_data:
            c -= (
                data["amount"]
                * Product.query.filter_by(id=data["product_id"]).first().price
            )

        self.assertEqual(user.credit, c)

    def test_multi_user_purchases(self):
        """Testing purchases done by multiple users"""
        users = User.query.all()
        for user in users:
            self.assertEqual(user.credit, 0)

        # Insert purchases
        p1 = Purchase(user_id=1, product_id=1, amount=5)
        p2 = Purchase(user_id=2, product_id=2, amount=2)
        p3 = Purchase(user_id=3, product_id=4, amount=1)
        p4 = Purchase(user_id=3, product_id=3, amount=6)
        for p in [p1, p2, p3, p4]:
            db.session.add(p)
        db.session.commit()

        # Check purchases
        purchases = Purchase.query.all()
        products = Product.query.all()
        self.assertEqual(len(purchases), 4)
        self.assertEqual(purchases[0].amount, 5)
        self.assertEqual(purchases[0].product_id, 1)
        self.assertEqual(purchases[0].price, 5 * products[0].price)
        self.assertEqual(purchases[1].amount, 2)
        self.assertEqual(purchases[1].product_id, 2)
        self.assertEqual(purchases[1].price, 2 * products[1].price)
        self.assertEqual(purchases[2].amount, 1)
        self.assertEqual(purchases[2].product_id, 4)
        self.assertEqual(purchases[2].price, 1 * products[3].price)
        self.assertEqual(purchases[3].amount, 6)
        self.assertEqual(purchases[3].product_id, 3)
        self.assertEqual(purchases[3].price, 6 * products[2].price)

        # Check users
        users = User.query.all()
        self.assertEqual(users[0].credit, -5 * products[0].price)
        self.assertEqual(len(users[0].purchases.all()), 1)
        self.assertEqual(users[1].credit, -2 * products[1].price)
        self.assertEqual(len(users[1].purchases.all()), 1)
        credit = 1 * products[3].price + 6 * products[2].price
        self.assertEqual(users[2].credit, -credit)
        self.assertEqual(len(users[2].purchases.all()), 2)
        self.assertEqual(users[3].credit, 0)
        self.assertEqual(len(users[3].purchases.all()), 0)

    def test_multiple_purchases_update_product_price(self):
        """This test is designed to ensure that purchases still show
        the correct price even after price changes of products."""

        # Generate timestamps for correct timing of purchases and updates
        t1 = datetime.datetime.now() - datetime.timedelta(seconds=30)
        t2 = datetime.datetime.now() - datetime.timedelta(seconds=25)
        t3 = datetime.datetime.now() - datetime.timedelta(seconds=20)
        t4 = datetime.datetime.now() - datetime.timedelta(seconds=15)
        t5 = datetime.datetime.now() - datetime.timedelta(seconds=10)
        t6 = datetime.datetime.now() - datetime.timedelta(seconds=5)
        # Update product price
        pp = ProductPrice(product_id=1, price=300, admin_id=1, timestamp=t1)
        db.session.add(pp)
        db.session.commit()
        # Get the first product price
        product = Product.query.filter_by(id=1).first()
        pr_1 = copy(product.price)
        # Do first purchase
        purchase = Purchase(user_id=1, product_id=1, amount=1, timestamp=t2)
        db.session.add(purchase)
        db.session.commit()
        # Update product price
        pp = ProductPrice(product_id=1, price=100, admin_id=1, timestamp=t3)
        db.session.add(pp)
        db.session.commit()
        # Get the second product price
        product = Product.query.filter_by(id=1).first()
        pr_2 = copy(product.price)
        # Do second purchase
        purchase = Purchase(user_id=1, product_id=1, amount=1, timestamp=t4)
        db.session.add(purchase)
        # Update product price
        pp = ProductPrice(product_id=1, price=600, admin_id=1, timestamp=t5)
        db.session.add(pp)
        db.session.commit()
        # Get the third product price
        product = Product.query.filter_by(id=1).first()
        pr_3 = copy(product.price)
        # Do third purchase
        purchase = Purchase(user_id=1, product_id=1, amount=1, timestamp=t6)
        db.session.add(purchase)
        db.session.commit()

        # Check the product prices
        self.assertEqual(pr_1, 300)
        self.assertEqual(pr_2, 100)
        self.assertEqual(pr_3, 600)

        # Check user credit
        user = User.query.filter_by(id=1).first()
        self.assertEqual(len(user.purchases.all()), 3)
        self.assertEqual(user.credit, -(pr_1 + pr_2 + pr_3))

        # Check purchase prices
        purchases = Purchase.query.all()
        self.assertEqual(purchases[0].price, 300)
        self.assertEqual(purchases[1].price, 100)
        self.assertEqual(purchases[2].price, 600)

    def test_purchase_revokes(self):
        """This unittest is designed to ensure, that purchase revokes will be
        applied to the user credit"""
        # Insert some purchases
        for _ in range(1, 11):
            purchase = Purchase(user_id=1, product_id=1, amount=1)
            db.session.add(purchase)
        db.session.commit()
        user = User.query.filter(User.id == 1).first()
        self.assertEqual(user.credit, -3000)
        # Revoke some purchases
        purchases = Purchase.query.all()
        purchases[0].set_revoked(revoked=True)
        purchases[4].set_revoked(revoked=True)
        purchases[6].set_revoked(revoked=True)
        db.session.commit()
        # Check user credit
        user = User.query.filter(User.id == 1).first()
        self.assertEqual(user.credit, -2100)
        # Un-Revoke one purchase
        purchases = Purchase.query.all()
        purchases[4].set_revoked(revoked=False)
        db.session.commit()
        # Check user credit
        user = User.query.filter(User.id == 1).first()
        self.assertEqual(user.credit, -2400)
