#!/usr/bin/env python3

from shopdb.api import *
from shopdb.models import *
from flask_testing import TestCase
from flask_bcrypt import Bcrypt
import configuration as config
import pdb
# Global password storage. Hashing the passwords for each unit test
# would take too long. For this reason, the passwords are created once
# and then stored in this array.
passwords = None

# Default data for users
u_firstnames = ['William', 'Mary', 'Bryce', 'Daniel']
u_lastnames = ['Jones', 'Smith', 'Jones', 'Lee']
u_usernames = ['alias1', 'alias2', 'alias3', 'alias4']
u_emails = ['william.jones@test.com', 'mary.smith@example.com',
            'bryce.jones@example.com', 'daniel.lee@example.com']
u_passwords = ['secret1', 'secret2', 'secret3', 'secret4']

# Default data for products
p_names = ['Pizza', 'Coffee', 'Cookie', 'Coke']
p_prices = [300, 50, 100, 200]

# Default data for ranks
r_names = ['Contender', 'Member', 'Alumni']
r_limits = [0, -2000, -2000]


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
                passwords[i] = self.bcrypt.generate_password_hash(pwds[i])
        return passwords

    def insert_default_users(self):
        hashes = self.generate_passwords(u_passwords)
        for i in range(0, len(u_firstnames)):
            user = User(
                firstname=u_firstnames[i],
                lastname=u_lastnames[i],
                username=u_usernames[i],
                email=u_emails[i],
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

    def test_default_users(self):
        """Check if all users have been entered correctly"""
        users = User.query.all()
        # Check number of users
        self.assertEqual(len(users), len(u_firstnames))

        for i in range(0, len(u_firstnames)):
            self.assertEqual(users[i].firstname, u_firstnames[i])
            self.assertEqual(users[i].lastname, u_lastnames[i])
            self.assertEqual(users[i].username, u_usernames[i])
            self.assertEqual(users[i].email, u_emails[i])
            self.assertTrue(bcrypt.check_password_hash(
                            users[i].password, u_passwords[i]))

    def test_insert_default_ranks(self):
        """Check if all ranks have been entered correctly"""
        ranks = Rank.query.all()
        self.assertEqual(len(ranks), len(r_names))
        for i in range(0, len(r_names)):
            self.assertEqual(ranks[i].name, r_names[i])

    def test_verify_all_users_except_last(self):
        """Check if all users except the last one have been verified"""
        users = User.query.all()
        for i in range(0, len(users) - 1):
            self.assertTrue(users[i].is_verified)
        self.assertEqual(users[0].rank_id, 2)
        self.assertEqual(users[1].rank_id, 3)
        self.assertEqual(users[2].rank_id, 1)
        self.assertFalse(users[-1].is_verified)
