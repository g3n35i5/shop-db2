from shopdb.api import *
import shopdb.models as models
import shopdb.exceptions as exc
from sqlalchemy.exc import *
from base import BaseTestCase
from copy import copy
import pdb


class UserModelTestCase(BaseTestCase):
    def test_user_representation(self):
        '''Testing the user representation'''
        user = User.query.filter_by(id=1).first()
        self.assertEqual(repr(user), '<User 1: Jones, William>')

    def test_get_user_purchases(self):
        '''Testing get user purchase list'''
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
        '''Test the password setter method'''
        user = User.query.filter_by(id=1).first()
        check = self.bcrypt.check_password_hash(user.password, 'test_password')
        self.assertFalse(check)
        user.password = self.bcrypt.generate_password_hash('test_password')
        db.session.commit()
        user = User.query.filter_by(id=1).first()
        check = self.bcrypt.check_password_hash(user.password, 'test_password')
        self.assertTrue(check)

    def test_insert_invalid_email(self):
        '''Test the regex match of the user email'''
        user = User.query.filter_by(id=1).first()
        backup_email = copy(user.email)
        for mail in ['test', 'test@test', '@test', 't@test.c', 'test@test-com',
                     't@test.com.', None, 2]:
            with self.assertRaises(exc.InvalidEmailAddress):
                user.email = mail
                db.session.commit()

            db.session.rollback()
        user = User.query.filter_by(id=1).first()
        self.assertEqual(user.email, backup_email)

    def test_verify_user_twice(self):
        '''Users cant be verified twice'''
        user = User.query.filter_by(id=1).first()
        self.assertTrue(user.is_verified)
        with self.assertRaises(exc.UserAlreadyVerified):
            user.verify(admin_id=1)
            db.session.commit()

        user = User.query.filter_by(id=1).first()
        self.assertTrue(user.is_verified)

    def test_verify_user(self):
        '''Verify a user. We take the last one in the list since all other
           usershave already been verified.'''
        user = User.query.order_by(User.id.desc()).first()
        self.assertFalse(user.is_verified)
        user.verify(admin_id=1)
        db.session.commit()
        user = User.query.order_by(User.id.desc()).first()
        self.assertTrue(user.is_verified)
        verification = (UserVerification.query
                        .order_by(UserVerification.id.desc())
                        .first())
        self.assertEqual(verification.user_id, user.id)
        self.assertEqual(verification.admin_id, 1)

    def test_set_user_rank_id(self):
        '''Update the user rank id'''
        user = User.query.filter_by(id=1).first()
        self.assertEqual(user.rank_id, None)
        self.assertEqual(user.rank, None)
        user.set_rank_id(rank_id=2, admin_id=1)
        db.session.commit()
        user = User.query.filter_by(id=1).first()
        self.assertEqual(user.rank_id, 2)
        self.assertEqual(user.rank, 'Member')
        with self.assertRaises(NothingHasChanged):
            user.set_rank_id(rank_id=2, admin_id=1)

    def test_update_user_firstname(self):
        '''Update the firstname of a user'''
        user = User.query.filter_by(id=1).first()
        self.assertEqual(user.id, 1)
        user.firstname = 'Updated_Firstname'
        db.session.commit()
        user = User.query.filter_by(id=1).first()
        self.assertEqual(user.firstname, 'Updated_Firstname')

    def test_update_user_lastname(self):
        '''Update the lastname of a user'''
        user = User.query.filter_by(id=1).first()
        self.assertEqual(user.id, 1)
        user.lastname = 'Updated_Lastname'
        db.session.commit()
        user = User.query.filter_by(id=1).first()
        self.assertEqual(user.lastname, 'Updated_Lastname')

    def test_duplicate_username(self):
        '''It should be ensured that the username is unique'''
        user1 = User.query.filter_by(id=1).first()
        user2 = User.query.filter_by(id=2).first()
        user2.username = user1.username
        with self.assertRaises(IntegrityError):
            db.session.commit()

    def test_duplicate_email(self):
        '''It should be ensured that the users email is unique'''
        user1 = User.query.filter_by(id=1).first()
        user2 = User.query.filter_by(id=2).first()
        user2.email = user1.email
        with self.assertRaises(IntegrityError):
            db.session.commit()

    def test_insert_purchase_as_non_verified_user(self):
        '''It must be ensured that non-verified users cannot make purchases.'''
        user = User.query.filter_by(id=4).first()
        self.assertFalse(user.is_verified)
        with self.assertRaises(exc.UserIsNotVerified):
            purchase = Purchase(user_id=4, product_id=1)
            db.session.add(purchase)
            db.session.commit()
        db.session.rollback()
        # No purchase may have been made at this point
        purchases = Purchase.query.all()
        self.assertEqual(len(purchases), 0)
