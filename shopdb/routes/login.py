#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import datetime
from flask import jsonify
import shopdb.exceptions as exc
import jwt
from shopdb.api import (app, convert_minimal, check_fields_and_types, json_body, bcrypt)
from shopdb.models import User


@app.route('/login', methods=['POST'], endpoint='login')
def login():
    """
    Registered users can log in on this route.

    :return:                    A temporary valid token, which users can use
                                to identify themselves when making requests to
                                the API.

    :raises DataIsMissing:      If the id or password (or both) is not included
                                in the request.
    :raises UnknownField:       If an unknown parameter exists in the request
                                data.
    :raises InvalidType:        If one or more parameters have an invalid type.
    :raises InvalidCredentials: If no user can be found with the given data.
    :raises UserIsNotVerified:  If the user has not yet been verified.
    """
    data = json_body()
    # Check all items in the json body.
    required = {'id': int, 'password': str}
    check_fields_and_types(data, required)

    # Try to get the user with the id
    user = User.query.filter_by(id=data['id']).first()

    # If no user with this data exists cancel the authentication.
    if not user:
        raise exc.InvalidCredentials()

    # Check if the user has already been verified.
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    # Check if the user is inactive
    if not user.active:
        raise exc.UserIsInactive()

    # Check if the user has set a password.
    if not user.password:
        raise exc.InvalidCredentials()

    # Check if the password matches the user's password.
    if not bcrypt.check_password_hash(user.password, str(data['password'])):
        raise exc.InvalidCredentials()

    # Create a dictionary object of the user.
    fields = ['id', 'firstname', 'lastname', 'credit']
    d_user = convert_minimal(user, fields)[0]

    # Create a token.
    exp = datetime.datetime.now() + datetime.timedelta(minutes=60)
    token = jwt.encode({'user': d_user, 'exp': exp}, app.config['SECRET_KEY'])

    # Return the result.
    return jsonify({'result': True, 'token': token.decode('UTF-8')}), 200
