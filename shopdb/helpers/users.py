#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from sqlalchemy.exc import IntegrityError

import shopdb.exceptions as exc
from shopdb.api import app, db, bcrypt
from shopdb.helpers.validators import check_fields_and_types
from shopdb.models import User


def insert_user(data):
    """
    This help function creates a new user with the given data.

    :param data:                 Is the dictionary containing the data for the
                                 new user.

    :return:                     None

    :raises DataIsMissing:       If not all required data is available.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises PasswordsDoNotMatch: If the passwords do not match.
    :raises CouldNotCreateEntry: If the new user cannot be created.
    """

    required = {'lastname': str}
    optional = {'firstname': str, 'password': str, 'password_repeat': str}

    check_fields_and_types(data, required, optional)

    password = None

    if 'password' in data:
        if 'password_repeat' not in data:
            raise exc.DataIsMissing()

        password = data['password'].strip()
        repeat_password = data['password_repeat'].strip()

        # Check if the passwords match.
        if password != repeat_password:
            raise exc.PasswordsDoNotMatch()

        # Check the password length
        if len(password) < app.config['MINIMUM_PASSWORD_LENGTH']:
            raise exc.PasswordTooShort()

        password = bcrypt.generate_password_hash(data['password'])

    # Try to create the user.
    if 'firstname' in data:
        firstname = data['firstname']
    else:
        firstname = None
    try:
        user = User(
            firstname=firstname,
            lastname=data['lastname'],
            password=password)
        db.session.add(user)
    except IntegrityError:
        raise exc.CouldNotCreateEntry()
