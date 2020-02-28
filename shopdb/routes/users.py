#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from flask import jsonify, request
from sqlalchemy.exc import IntegrityError

import shopdb.exceptions as exc
from shopdb.api import app, db, bcrypt
from shopdb.helpers.decorators import adminRequired, adminOptional, checkIfUserIsValid
from shopdb.helpers.query import QueryFromRequestParameters
from shopdb.helpers.users import insert_user
from shopdb.helpers.utils import convert_minimal, json_body
from shopdb.helpers.updater import generic_update
from shopdb.models import User


@app.route('/users', methods=['GET'])
@adminOptional
def list_users(admin):
    """
    Returns a list of all users. If this route is called by an
    administrator, all information is returned. However, if it is called
    without further rights, a minimal version is returned.

    :param admin: Is the administrator user, determined by @adminOptional.

    :return:      A list of all users.
    """

    # Define fields
    if admin is None:
        fields = ['id', 'firstname', 'lastname', 'fullname', 'rank_id', 'imagename']
    else:
        fields = ['id', 'firstname', 'lastname', 'fullname', 'credit', 'rank_id', 'imagename', 'active',
                  'is_admin', 'creation_date', 'verification_date', 'is_verified']

    query = QueryFromRequestParameters(User, request.args, fields=fields)

    # Hide non verified, inactive and system users for non-administrators
    if admin is None:
        query = (query
                 .filter(User.is_verified.is_(True))
                 .filter(User.active.is_(True))
                 .filter(User.is_system_user.is_(False)))

    result, content_range = query.result()
    response = jsonify(convert_minimal(result, fields))
    response.headers['Content-Range'] = content_range
    return response


@app.route('/users', methods=['POST'])
def create_user():
    """
    Registration of new users.

    :return:                     A message that the registration was successful.

    :raises CouldNotCreateEntry: If the new user cannot be created.
    """
    insert_user(json_body())
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created user.'}), 200


@app.route('/users/<int:id>/favorites', methods=['GET'])
@checkIfUserIsValid
def get_user_favorites(user, id):
    """
    Returns a list with the IDs of a user's favorite products. The list is
    empty if no favourite products exist.

    :param user:               Is the user, determined by @checkIfUserIsValid.
    :param id:                 Is the user id.

    :return:                   A list with the IDs of the favorite products.
    """

    return jsonify(user.favorites), 200


@app.route('/users/<int:id>/deposits', methods=['GET'])
@checkIfUserIsValid
def get_user_deposits(user, id):
    """
    Returns a list with all deposits of a user.

    :param user:               Is the user, determined by @checkIfUserIsValid.
    :param id:                 Is the user id.

    :return:                   A list with all deposits of the user.
    """

    fields = ['id', 'timestamp', 'admin_id', 'amount', 'revoked', 'comment']
    deposits = convert_minimal(user.deposits.all(), fields)

    return jsonify(deposits), 200


@app.route('/users/<int:id>/purchases', methods=['GET'])
@checkIfUserIsValid
def get_user_purchases(user, id):
    """
    Returns a list with all purchases of a user.

    :param user:               Is the user, determined by @checkIfUserIsValid.
    :param id:                 Is the user id.

    :return:                   A list with all purchases of the user.
    """

    fields = ['id', 'timestamp', 'product_id', 'productprice', 'amount', 'revoked', 'price']
    purchases = convert_minimal(user.purchases.all(), fields)

    return jsonify(purchases), 200


@app.route('/users/<int:id>', methods=['GET'])
@adminOptional
def get_user(admin, id):
    """
    Returns the user with the requested id.

    :param user:               Is the user, determined by @checkIfUserIsValid.
    :param id:                 Is the user id.

    :return:                   The requested user as JSON object.
    """
    # Query user
    user = User.query.filter(User.id == id).first()
    if not user:
        raise exc.EntryNotFound()

    if admin is None:
        # Check if the user has been verified.
        if not user.is_verified:
            raise exc.UserIsNotVerified()
        # Check if the user is inactive
        if not user.active:
            raise exc.UserIsInactive()

    fields = ['id', 'firstname', 'lastname', 'fullname', 'credit', 'rank_id', 'imagename', 'active',
              'is_admin', 'creation_date', 'verification_date', 'is_verified']
    user = convert_minimal(user, fields)[0]
    return jsonify(user), 200


@app.route('/users/<int:id>', methods=['PUT'])
@adminRequired
def update_user(admin, id):
    """
    Update the user with the given id.

    :param admin: Is the administrator user, determined by @adminRequired.
    :param id:    Is the user id.

    :return:      A message that the update was successful and a list of all updated fields.
    """
    # Get the update data
    data = json_body()

    # Query the user. If he/she is not verified yet, there *must* be a
    # rank_id given in the update data.
    user = User.query.filter(User.id == id).first()
    if not user:
        raise exc.EntryNotFound()

    if not user.is_verified and 'rank_id' not in data:
        raise exc.UserIsNotVerified()

    # The password pre-check must be done here...
    if 'password' in data:
        # The repeat password must be there, too!
        if 'password_repeat' not in data:
            raise exc.DataIsMissing()

        # Both must be strings
        if not all([isinstance(x, str) for x in [data['password'], data['password_repeat']]]):
            raise exc.WrongType()

        # Passwords must match
        if data['password'] != data['password_repeat']:
            raise exc.PasswordsDoNotMatch()

        # Minimum password length
        if len(data['password']) < app.config['MINIMUM_PASSWORD_LENGTH']:
            raise exc.PasswordTooShort()

        # Convert the password into a salted hash
        # DONT YOU DARE TO REMOVE THIS LINE
        data['password'] = bcrypt.generate_password_hash(data['password'])
        # DONT YOU DARE TO REMOVE THIS LINE

        # All fine, delete repeat_password from the dict and do the rest of the update
        del data['password_repeat']

    return generic_update(User, id, data, admin)


@app.route('/users/<int:id>', methods=['DELETE'])
@adminRequired
def delete_user(admin, id):
    """
    Delete a user. This is only possible if the user has not yet been verified.

    :param admin:                 Is the administrator user, determined by
                                  @adminRequired.
    :param id:                    Is the user id.

    :return:                      A message that the deletion was successful.

    :raises EntryNotFound:        If the user with this ID does not exist.
    :raises EntryCanNotBeDeleted: If the user has already been verified or the
                                  deletion cannot take place for any other
                                  reason.
    """
    # Check if the user exists
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.EntryNotFound()

    # Check if the user has been verified
    if user.is_verified:
        raise exc.EntryCanNotBeDeleted()

    # Delete the user
    try:
        db.session.delete(user)
        db.session.commit()
    except IntegrityError:
        raise exc.EntryCanNotBeDeleted()

    return jsonify({'message': 'User deleted.'}), 200
