#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask_testing import TestCase

import configuration as config
from shop_db2.api import app, bcrypt, db, set_app
from shop_db2.models import (
    AdminUpdate,
    Deposit,
    Product,
    Purchase,
    Rank,
    Replenishment,
    ReplenishmentCollection,
    Stocktaking,
    StocktakingCollection,
    Tag,
    User,
)

# Global password storage. Hashing the passwords for each unit test
# would take too long. For this reason, the passwords are created once
# and then stored in this array.
passwords = None

# Default data for users
user_data = [
    {"firstname": "William", "lastname": "Jones", "password": "secret1"},
    {"firstname": "Mary", "lastname": "Smith", "password": "secret2"},
    {"firstname": "Bryce", "lastname": "Jones", "password": None},
    {"firstname": "Daniel", "lastname": "Lee", "password": None},
    {"firstname": None, "lastname": "Seller", "password": None},
]

# Default data for products
product_data = [
    {"name": "Pizza", "price": 300, "tags": [1]},
    {"name": "Coffee", "price": 50, "tags": [2]},
    {"name": "Cookie", "price": 100, "tags": [3]},
    {"name": "Coke", "price": 200, "tags": [4]},
]

# Default data for ranks
rank_data = [
    {"name": "Contender", "debt_limit": 0},
    {"name": "Member", "debt_limit": -2000},
    {"name": "Alumni", "debt_limit": -1000},
    {"name": "Inactive", "debt_limit": 0, "active": False},
]

# Default data for product tags
tag_data = [
    {"name": "Food"},
    {"name": "Sweets"},
    {"name": "Drinks"},
    {"name": "Coffee"},
    {"name": "Uncategorized", "is_for_sale": False},
]


class BaseTestCase(TestCase):
    def create_app(self):
        return set_app(config.UnittestConfig)

    def setUp(self):
        # Create tables
        db.create_all()
        db.session.commit()
        # Create test client
        self.client = app.test_client()
        self.bcrypt = bcrypt
        # Insert default data
        self.insert_default_users()
        self.insert_first_admin()
        self.verify_all_users_except_last()
        self.insert_default_ranks()
        self.insert_default_tags()
        self.insert_default_products()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def generate_passwords(self, password_list):
        """This function generates hashes of passwords and stores them in the
        global variable so that they do not have to be created again.
        """
        global passwords
        if passwords is None:
            passwords = [None] * len(password_list)
            for index, password in enumerate(password_list):
                if password:
                    passwords[index] = self.bcrypt.generate_password_hash(password)
                else:
                    passwords[index] = None
        return passwords

    def insert_default_users(self):
        hashes = self.generate_passwords(list(map(lambda u: u["password"], user_data)))
        for index, data in enumerate(user_data):
            user = User(
                firstname=data["firstname"],
                lastname=data["lastname"],
                password=hashes[index],
            )
            db.session.add(user)

        db.session.commit()

    @staticmethod
    def insert_first_admin():
        au = AdminUpdate(user_id=1, admin_id=1, is_admin=True)
        db.session.add(au)
        db.session.commit()

    @staticmethod
    def insert_default_tag_assignments():
        for p_data in product_data:
            product = Product.query.filter(Product.name == p_data["name"]).first()
            tag = Tag.query.filter(Tag.id == p_data["tags"][0]).first()
            product.tags.append(tag)

        db.session.commit()

    @staticmethod
    def insert_default_products():
        for data in product_data:
            product = Product(name=data["name"], created_by=1)
            db.session.add(product)
            db.session.flush()  # This is needed so that the product has its id
            product.set_price(price=data["price"], admin_id=1)

        db.session.commit()

    @staticmethod
    def insert_default_ranks():
        for rank in rank_data:
            db.session.add(Rank(**rank))
        db.session.commit()

    @staticmethod
    def verify_all_users_except_last():
        users = User.query.all()
        users[0].verify(admin_id=1, rank_id=2)
        users[1].verify(admin_id=1, rank_id=3)
        users[2].verify(admin_id=1, rank_id=1)
        users[4].verify(admin_id=1, rank_id=1)

        db.session.commit()

    @staticmethod
    def insert_default_tags():
        for data in tag_data:
            tag = Tag(**data, created_by=1)
            db.session.add(tag)
        db.session.commit()

    @staticmethod
    def insert_default_replenishmentcollections():
        product1 = Product.query.filter_by(id=1).first()
        product2 = Product.query.filter_by(id=2).first()
        product3 = Product.query.filter_by(id=3).first()
        rc1 = ReplenishmentCollection(admin_id=1, revoked=False, comment="Foo", seller_id=5)
        rc2 = ReplenishmentCollection(admin_id=2, revoked=False, comment="Foo", seller_id=5)
        for r in [rc1, rc2]:
            db.session.add(r)
        db.session.flush()
        rep1 = Replenishment(
            replcoll_id=rc1.id,
            product_id=product1.id,
            amount=10,
            total_price=10 * product1.price,
        )
        rep2 = Replenishment(
            replcoll_id=rc1.id,
            product_id=product2.id,
            amount=20,
            total_price=20 * product2.price,
        )
        rep3 = Replenishment(
            replcoll_id=rc2.id,
            product_id=product3.id,
            amount=5,
            total_price=5 * product3.price,
        )
        rep4 = Replenishment(
            replcoll_id=rc2.id,
            product_id=product1.id,
            amount=10,
            total_price=10 * product1.price,
        )
        for r in [rep1, rep2, rep3, rep4]:
            db.session.add(r)
        db.session.commit()

    @staticmethod
    def insert_default_stocktakingcollections():
        db.session.add(StocktakingCollection(admin_id=1))
        db.session.add(StocktakingCollection(admin_id=1))
        db.session.flush()

        stocktakings = [
            {"product_id": 1, "count": 100},
            {"product_id": 2, "count": 50},
            {"product_id": 3, "count": 25},
            {"product_id": 4, "count": 33},
        ]
        for s in stocktakings:
            db.session.add(Stocktaking(**s, collection_id=1))

        stocktakings = [
            {"product_id": 1, "count": 50},
            {"product_id": 2, "count": 25},
            {"product_id": 3, "count": 12},
            {"product_id": 4, "count": 3},
        ]
        for s in stocktakings:
            db.session.add(Stocktaking(**s, collection_id=2))
        db.session.commit()

    @staticmethod
    def insert_default_purchases():
        p1 = Purchase(user_id=1, product_id=1, amount=1)
        p2 = Purchase(user_id=2, product_id=3, amount=2)
        p3 = Purchase(user_id=2, product_id=2, amount=4)
        p4 = Purchase(user_id=3, product_id=1, amount=6)
        p5 = Purchase(user_id=1, product_id=3, amount=8)
        for p in [p1, p2, p3, p4, p5]:
            db.session.add(p)
        db.session.commit()

    @staticmethod
    def insert_default_deposits():
        d1 = Deposit(user_id=1, amount=100, admin_id=1, comment="Test deposit")
        d2 = Deposit(user_id=2, amount=200, admin_id=1, comment="Test deposit")
        d3 = Deposit(user_id=2, amount=500, admin_id=1, comment="Test deposit")
        d4 = Deposit(user_id=3, amount=300, admin_id=1, comment="Test deposit")
        d5 = Deposit(user_id=1, amount=600, admin_id=1, comment="Test deposit")
        for d in [d1, d2, d3, d4, d5]:
            db.session.add(d)
        db.session.commit()
