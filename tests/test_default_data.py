from shopdb.api import *
from tests.base import BaseTestCase
from tests.base import u_passwords, u_firstnames, u_lastnames, r_names


class DefaultDataTest(BaseTestCase):
    def test_default_users(self):
        """Check if all users have been entered correctly"""
        users = User.query.all()
        # Check number of users
        self.assertEqual(len(users), len(u_firstnames))

        for i in range(0, len(u_firstnames)):
            self.assertEqual(users[i].firstname, u_firstnames[i])
            self.assertEqual(users[i].lastname, u_lastnames[i])
            if u_passwords[i]:
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
