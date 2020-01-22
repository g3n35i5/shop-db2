#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from sqlalchemy.exc import IntegrityError
from flask import jsonify, request
import shopdb.exceptions as exc
from shopdb.helpers.decorators import adminRequired, adminOptional, checkIfUserIsValid
from shopdb.helpers.validators import check_fields_and_types, check_forbidden
from shopdb.helpers.utils import convert_minimal, update_fields, json_body
from shopdb.helpers.query import QueryFromRequestParameters
from shopdb.helpers.users import insert_user
from shopdb.api import app, db, bcrypt
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

    query = QueryFromRequestParameters(User, request.args)
    # Hide non verified and inactive users for non-administrators
    if admin is None:
        fields = ['id', 'firstname', 'lastname', 'rank_id']
        query = (query
                 .filter(User.is_verified.is_(True))
                 .filter(User.active.is_(True)))
    else:
        fields = ['id', 'firstname', 'lastname', 'credit', 'is_admin', 'creation_date', 'rank_id', 'is_verified']
    result, content_range = query.result()
    response = jsonify(convert_minimal(result, fields))
    response.headers['Content-Range'] = content_range
    return response



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


@app.route('/users/<int:id>/refunds', methods=['GET'])
@checkIfUserIsValid
def get_user_refunds(user, id):
    """
    Returns a list with all refunds of a user.

    :param user:               Is the user, determined by @checkIfUserIsValid.
    :param id:                 Is the user id.

    :return:                   A list with all refunds of the user.
    """

    fields = ['id', 'timestamp', 'admin_id', 'total_price', 'revoked', 'comment']
    refunds = convert_minimal(user.refunds.all(), fields)

    return jsonify(refunds), 200


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
@checkIfUserIsValid
def get_user(user, id):
    """
    Returns the user with the requested id.

    :param user:               Is the user, determined by @checkIfUserIsValid.
    :param id:                 Is the user id.

    :return:                   The requested user as JSON object.
    """

    fields = ['id', 'firstname', 'lastname', 'credit', 'rank_id', 'is_admin', 'creation_date', 'verification_date']
    user = convert_minimal(user, fields)[0]
    return jsonify(user), 200


@app.route('/users/<int:id>', methods=['PUT'])
@adminRequired
def update_user(admin, id):
    """
    Update the user with the given id.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the user id.
    :return:                     A message that the update was
                                 successful and a list of all updated fields.

    :raises EntryNotFound:        If the user with this ID does not exist.
    :raises UserIsNotVerified:   If the user has not yet been verified.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid type.
    :raises PasswordsDoNotMatch: If the password and its repetition do not
                                 match.
    :raises DataIsMissing:       If the password is to be updated but no
                                 repetition of the password exists in the
                                 request.
    """
    data = json_body()

    # Query user
    user = User.query.filter(User.id == id).first()
    if not user:
        raise exc.EntryNotFound()

    # Raise an exception if the user has not been verified yet.
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    allowed = {
        'firstname': str,
        'lastname': str,
        'password': str,
        'password_repeat': str,
        'is_admin': bool,
        'rank_id': int}

    # Check the data for forbidden fields.
    check_forbidden(data, allowed, user)
    # Check all allowed fields and for their types.
    check_fields_and_types(data, None, allowed)

    updated_fields = []

    # Update admin role
    if 'is_admin' in data:
        user.set_admin(is_admin=data['is_admin'], admin_id=admin.id)
        if not user.is_admin:
            users = User.query.all()
            admins = list(filter(lambda x: x.is_admin, users))
            if not admins:
                raise exc.NoRemainingAdmin()

        updated_fields.append('is_admin')
        del data['is_admin']

    # Update rank
    if 'rank_id' in data:
        user.set_rank_id(rank_id=data['rank_id'], admin_id=admin.id)
        updated_fields.append('rank_id')
        del data['rank_id']

    # Check password
    if 'password' in data:
        if 'password_repeat' in data:
            password = data['password'].strip()
            password_repeat = data['password_repeat'].strip()

            if password != password_repeat:
                raise exc.PasswordsDoNotMatch()

            if len(password) < app.config['MINIMUM_PASSWORD_LENGTH']:
                raise exc.PasswordTooShort()
            user.password = bcrypt.generate_password_hash(password)
            updated_fields.append('password')
            del data['password_repeat']
        else:
            raise exc.DataIsMissing()

        del data['password']

    # All other fields
    updateable = ['firstname', 'lastname']
    check_forbidden(data, updateable, user)
    updated_fields = update_fields(data, user, updated=updated_fields)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Updated user.',
        'updated_fields': updated_fields
    }), 201


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
