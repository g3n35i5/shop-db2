#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

import argparse
import getpass
import os
import sys

from sqlalchemy.exc import IntegrityError

import configuration as config
import shopdb.exceptions as exc
from shopdb.api import app, db, set_app
from shopdb.helpers.users import insert_user
from shopdb.models import Rank, User


def _get_password():
    """
    Ask the user for a password and repeat it until both passwords match and
    are not empty.

    :return: The password as plaintext.
    """
    password = None
    rep_password = None

    while not password or password != rep_password:
        password = getpass.getpass(prompt="password: ")
        rep_password = getpass.getpass(prompt="repeat password: ")

        if password != rep_password:
            password = None
            rep_password = None
            print("Passwords do not match! Please try again.\n")

    return password


def input_user():
    """
    Prompts the user to enter the name and lastname of the first user
    (administrator) and then his password.

    :return: The firstname, the lastname and the password.
    """
    print("Please enter the data for the first user:")
    firstname = None
    while firstname in [None, ""]:
        firstname = input("firstname: ")
    lastname = None
    while lastname in [None, ""]:
        lastname = input("lastname: ")

    password = _get_password()

    return firstname, lastname, password


def create_database(argv):
    set_app(config.ProductiveConfig)
    app.app_context().push()
    db.create_all()
    db.session.commit()
    rank1 = Rank(name="Member", debt_limit=-2000)
    rank2 = Rank(name="Alumni", debt_limit=-2000)
    rank3 = Rank(name="Contender", debt_limit=0)
    rank4 = Rank(name="Inactive", debt_limit=0, active=False)
    try:
        for r in (rank1, rank2, rank3, rank4):
            db.session.add(r)
        db.session.commit()
    except IntegrityError:
        os.remove(config.ProductiveConfig.DATABASE_PATH)
        sys.exit("ERROR: Could not create database!")

    # Handle the user.
    parser: argparse.ArgumentParser = argparse.ArgumentParser("Setup script for shop-db2")
    parser.add_argument("-f", "-first-name", dest="firstname", help="First name of the admin user")
    parser.add_argument("-l", "-last-name", dest="lastname", help="Last name of the admin user")
    parser.add_argument("-p", "-password", dest="password", help="Password for the admin user")

    arguments: argparse.Namespace = parser.parse_args()
    firstname, lastname, password = arguments.firstname, arguments.lastname, arguments.password

    if any([x is None for x in [firstname, lastname, password]]):
        firstname, lastname, password = input_user()

    user = {
        "firstname": firstname,
        "lastname": lastname,
        "password": password,
        "password_repeat": password,
    }
    try:
        insert_user(user)
    except exc.PasswordTooShort:
        os.remove(config.ProductiveConfig.DATABASE_PATH)
        sys.exit(
            ("ERROR: Password to short. Needs at least {} characters." + " Aborting setup.").format(
                config.BaseConfig.MINIMUM_PASSWORD_LENGTH
            )
        )

    # Get the User
    user = User.query.filter_by(id=1).first()

    # Add User as Admin (is_admin, admin_id)
    user.set_admin(True, 1)

    # Verify the user (admin_id, rank_id)
    user.verify(1, 1)
    db.session.commit()


if __name__ == "__main__":
    db_exists = os.path.isfile(config.ProductiveConfig.DATABASE_PATH)
    if db_exists:
        sys.exit("ERROR: The database already exists!")
    try:
        create_database(sys.argv[1:])
    except KeyboardInterrupt:
        print("\n")
        os.remove(config.ProductiveConfig.DATABASE_PATH)
