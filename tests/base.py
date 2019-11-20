#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
from shopdb.api import db, set_app, app, bcrypt
from flask_testing import TestCase
import configuration as config

# Global password storage. Hashing the passwords for each unit test
# would take too long. For this reason, the passwords are created once
# and then stored in this array.
passwords = None

# Default data for users
u_firstnames = ['William', 'Mary', 'Bryce', 'Daniel']
u_lastnames = ['Jones', 'Smith', 'Jones', 'Lee']
u_passwords = ['secret1', 'secret2', None, None]

# Default data for products
p_names = ['Pizza', 'Coffee', 'Cookie', 'Coke']
p_prices = [300, 50, 100, 200]

# Default data for ranks
rank_data = [
        {'name': 'Contender', 'debt_limit': 0},
        {'name': 'Member', 'debt_limit': -2000},
        {'name': 'Alumni', 'debt_limit': -1000},
        {'name': 'Inactive', 'debt_limit': 0, 'active': False}]

# Default data for product tags
t_names = ['Food', 'Sweets', 'Drinks', 'Coffee']

# Default data for turnovers
turnovers = [
    {'admin_id': 1, 'amount': 200, 'comment': 'Turnover comment 1'},
    {'admin_id': 1, 'amount': 100, 'comment': 'Turnover comment 2'},
    {'admin_id': 1, 'amount': -100, 'comment': 'Turnover comment 3'},
    {'admin_id': 1, 'amount': -500, 'comment': 'Turnover comment 4'}
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
        self.insert_default_turnovers()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def generate_passwords(self, pwds):
        """This function generates hashes of passwords and stores them in the
           global variable so that they do not have to be created again."""
        global passwords
        if passwords is None:
            passwords = [None] * len(pwds)
            for i in range(0, len(pwds)):
                password = pwds[i]
                if password:
                    passwords[i] = self.bcrypt.generate_password_hash(password)
                else:
                    passwords[i] = None
        return passwords

    def insert_default_users(self):
        hashes = self.generate_passwords(u_passwords)
        for i in range(0, len(u_firstnames)):
            user = User(
                firstname=u_firstnames[i],
                lastname=u_lastnames[i],
                password=hashes[i])
            db.session.add(user)

        db.session.commit()

    def insert_first_admin(self):
        au = AdminUpdate(user_id=1, admin_id=1, is_admin=True)
        db.session.add(au)
        db.session.commit()

    def insert_default_products(self):
        for i in range(0, len(p_names)):
            product = Product(name=p_names[i], created_by=1)
            db.session.add(product)
            db.session.flush()  # This is needed so that the product has its id
            product.set_price(price=p_prices[i], admin_id=1)

        db.session.commit()

    def insert_default_ranks(self):
        for rank in rank_data:
            db.session.add(Rank(**rank))
        db.session.commit()

    def verify_all_users_except_last(self):
        users = User.query.all()
        users[0].verify(admin_id=1, rank_id=2)
        users[1].verify(admin_id=1, rank_id=3)
        users[2].verify(admin_id=1, rank_id=1)

        db.session.commit()

    def insert_default_tags(self):
        for name in t_names:
            tag = Tag(name=name, created_by=1)
            db.session.add(tag)
        db.session.commit()

    def insert_default_replenishmentcollections(self):
        product1 = Product.query.filter_by(id=1).first()
        product2 = Product.query.filter_by(id=2).first()
        product3 = Product.query.filter_by(id=3).first()
        rc1 = ReplenishmentCollection(admin_id=1, revoked=False, comment='Foo')
        rc2 = ReplenishmentCollection(admin_id=2, revoked=False, comment='Foo')
        for r in [rc1, rc2]:
            db.session.add(r)
        db.session.flush()
        rep1 = Replenishment(replcoll_id=rc1.id, product_id=product1.id,
                             amount=10, total_price=10 * product1.price)
        rep2 = Replenishment(replcoll_id=rc1.id, product_id=product2.id,
                             amount=20, total_price=20 * product2.price)
        rep3 = Replenishment(replcoll_id=rc2.id, product_id=product3.id,
                             amount=5, total_price=5 * product3.price)
        rep4 = Replenishment(replcoll_id=rc2.id, product_id=product1.id,
                             amount=10, total_price=10 * product1.price)
        for r in [rep1, rep2, rep3, rep4]:
            db.session.add(r)
        db.session.commit()

    def insert_default_stocktakingcollections(self):
        db.session.add(StocktakingCollection(admin_id=1))
        db.session.add(StocktakingCollection(admin_id=1))
        db.session.flush()

        stocktakings = [
            {'product_id': 1, 'count': 100},
            {'product_id': 2, 'count': 50},
            {'product_id': 3, 'count': 25},
            {'product_id': 4, 'count': 33}
        ]
        for s in stocktakings:
            db.session.add(Stocktaking(**s, collection_id=1))

        stocktakings = [
            {'product_id': 1, 'count': 50},
            {'product_id': 2, 'count': 25},
            {'product_id': 3, 'count': 12},
            {'product_id': 4, 'count': 3}
        ]
        for s in stocktakings:
            db.session.add(Stocktaking(**s, collection_id=2))
        db.session.commit()

    def insert_default_purchases(self):
        p1 = Purchase(user_id=1, product_id=1, amount=1)
        p2 = Purchase(user_id=2, product_id=3, amount=2)
        p3 = Purchase(user_id=2, product_id=2, amount=4)
        p4 = Purchase(user_id=3, product_id=1, amount=6)
        p5 = Purchase(user_id=1, product_id=3, amount=8)
        for p in [p1, p2, p3, p4, p5]:
            db.session.add(p)
        db.session.commit()

    def insert_default_deposits(self):
        d1 = Deposit(user_id=1, amount=100, admin_id=1, comment='Test deposit')
        d2 = Deposit(user_id=2, amount=200, admin_id=1, comment='Test deposit')
        d3 = Deposit(user_id=2, amount=500, admin_id=1, comment='Test deposit')
        d4 = Deposit(user_id=3, amount=300, admin_id=1, comment='Test deposit')
        d5 = Deposit(user_id=1, amount=600, admin_id=1, comment='Test deposit')
        for d in [d1, d2, d3, d4, d5]:
            db.session.add(d)
        db.session.commit()

    def insert_default_refunds(self):
        r1 = Refund(user_id=1, total_price=100, admin_id=1,
                    comment='Test refund')
        r2 = Refund(user_id=2, total_price=200, admin_id=1,
                    comment='Test refund')
        r3 = Refund(user_id=2, total_price=500, admin_id=1,
                    comment='Test refund')
        r4 = Refund(user_id=3, total_price=300, admin_id=1,
                    comment='Test refund')
        r5 = Refund(user_id=1, total_price=600, admin_id=1,
                    comment='Test refund')
        for r in [r1, r2, r3, r4, r5]:
            db.session.add(r)
        db.session.commit()

    def insert_default_payoffs(self):
        p1 = Payoff(amount=100, admin_id=1, comment='Test payoff 1')
        p2 = Payoff(amount=200, admin_id=1, comment='Test payoff 2')
        p3 = Payoff(amount=-50, admin_id=1, comment='Test payoff 3')
        for p in [p1, p2, p3]:
            db.session.add(p)
        db.session.commit()

    def insert_default_turnovers(self):
        for turnover in turnovers:
            db.session.add(Turnover(**turnover))
        db.session.commit()
