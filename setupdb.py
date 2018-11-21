#!/usr/bin/env python3

import sys
import os
import getpass
from sqlalchemy.exc import IntegrityError
from shopdb.models import User, Rank
from shopdb.api import app, db, set_app, insert_user
import configuration as config


def _get_password():
    """
    Ask the user for a password and repeat it until both passwords match and
    are not empty.

    :return: The password as plaintext.
    """
    password = None
    rep_password = None

    while not password or password != rep_password:
        password = getpass.getpass(prompt='password: ')
        rep_password = getpass.getpass(prompt='repeat password: ')

        if password != rep_password:
            password = None
            rep_password = None
            print('Passwords do not match! Please try again.\n')

    return password


def input_user():
    """
    Prompts the user to enter the name and lastname of the first user
    (administrator) and then his password.

    :return: The firstname, the lastname and the password.
    """
    print('Please enter the data for the first user:')
    firstname = None
    while firstname in [None, '']:
        firstname = input('firstname: ')
    lastname = None
    while lastname in [None, '']:
        lastname = input('lastname: ')

    password = _get_password()

    return firstname, lastname, password


def create_database():
    set_app(config.ProductiveConfig)
    app.app_context().push()
    db.create_all()
    db.session.commit()
    rank1 = Rank(name='Member', debt_limit=-2000)
    rank2 = Rank(name='Alumni', debt_limit=-2000)
    rank3 = Rank(name='Contender', debt_limit=0)
    try:
        for r in (rank1, rank2, rank3):
            db.session.add(r)
        db.session.commit()
    except IntegrityError:
        sys.exit('ERROR: Could not create database!')

    # Handle the user.
    firstname, lastname, password = input_user()
    user = {
        'firstname': firstname, 'lastname': lastname,
        'password': password, 'password_repeat': password
    }
    insert_user(user)

    # Get the User
    user = User.query.filter_by(id=1).first()

    # Add User as Admin (is_admin, admin_id)
    user.set_admin(True, 1)

    # Verify the user (admin_id, rank_id)
    user.verify(1, 1)
    db.session.commit()


if __name__ == '__main__':
    db_exists = os.path.isfile(config.ProductiveConfig.DATABASE_PATH)
    if db_exists:
        sys.exit('ERROR: The database already exists!')

    create_database()
