#!/usr/bin/env python3

from shopdb.api import *
from shopdb.models import *
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
r_names = ['Contender', 'Member', 'Alumni']
r_limits = [0, -2000, -2000]

# Default data for product tags
t_names = ['Food', 'Sweets', 'Drinks', 'Coffee']


class BaseTestCase(TestCase):
    def create_app(self):
        app.config.from_object(config.UnittestConfig)
        return app

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
        for i in range(0, len(r_names)):
            rank = Rank(name=r_names[i], debt_limit=r_limits[i])
            db.session.add(rank)
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

    def insert_default_payoffs(self):
        p1 = Payoff(amount=100, admin_id=1, comment='Test payoff 1')
        p2 = Payoff(amount=200, admin_id=1, comment='Test payoff 2')
        for p in [p1, p2]:
            db.session.add(p)
        db.session.commit()
