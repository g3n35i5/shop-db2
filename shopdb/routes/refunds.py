#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from sqlalchemy.exc import IntegrityError
from flask import jsonify
import shopdb.exceptions as exc
from shopdb.helpers.decorators import adminRequired
from shopdb.api import (app, convert_minimal, db, check_fields_and_types, check_forbidden, json_body)
from shopdb.models import Refund, User


@app.route('/refunds', methods=['GET'])
@adminRequired
def list_refunds(admin):
    """
    Returns a list of all refunds.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A list of all refunds.
    """
    refunds = Refund.query.all()
    fields = ['id', 'timestamp', 'user_id', 'total_price', 'comment',
              'revoked', 'admin_id']
    return jsonify({'refunds': convert_minimal(refunds, fields)}), 200


@app.route('/refunds/<int:id>', methods=['GET'])
def get_refund(id):
    """
    Returns the refund with the requested id.

    :param id:             Is the refund id.

    :return:               The requested refund as JSON object.

    :raises EntryNotFound: If the refund with this ID does not exist.
    """
    # Query the refund
    res = Refund.query.filter_by(id=id).first()
    # If it not exists, return an error
    if not res:
        raise exc.EntryNotFound()
    # Convert the refund to a JSON friendly format
    fields = ['id', 'timestamp', 'user_id', 'total_price', 'comment', 'revoked',
              'revokehistory']
    return jsonify({'refund': convert_minimal(res, fields)[0]}), 200


@app.route('/refunds', methods=['POST'])
@adminRequired
def create_refund(admin):
    """
    Insert a new refund.

    :param admin:                Is the administrator user, determined by @adminRequired.

    :return:                     A message that the creation was successful.

    :raises DataIsMissing:       If not all required data is available.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises EntryNotFound:       If the user with this ID does not exist.
    :raises UserIsNotVerified:   If the user has not yet been verified.
    :raises InvalidAmount:       If amount is equal to zero.
    :raises CouldNotCreateEntry: If any other error occurs.
    """
    data = json_body()
    required = {'user_id': int, 'total_price': int, 'comment': str}
    check_fields_and_types(data, required)

    user = User.query.filter_by(id=data['user_id']).first()
    if not user:
        raise exc.EntryNotFound()

    # Check if the user has been verified.
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    # Check if the user is inactive
    if not user.active:
        raise exc.UserIsInactive()

    # Check amount
    if data['total_price'] <= 0:
        raise exc.InvalidAmount()

    # Create and insert refund
    try:
        refund = Refund(**data)
        refund.admin_id = admin.id
        db.session.add(refund)
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created refund.'}), 200


@app.route('/refunds/<int:id>', methods=['PUT'])
@adminRequired
def update_refund(admin, id):
    """
    Update the refund with the given id.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the refund id.

    :return:                     A message that the update was
                                 successful and a list of all updated fields.

    :raises EntryNotFound:       If the refund with this ID does not exist.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid
                                 type.
    :raises NothingHasChanged:   If no change occurred after the update.
    :raises CouldNotUpdateEntry: If any other error occurs.
    """
    # Check refund
    refund = Refund.query.filter_by(id=id).first()
    if not refund:
        raise exc.EntryNotFound()

    data = json_body()

    if not data:
        raise exc.NothingHasChanged()

    updateable = {'revoked': bool}
    check_forbidden(data, updateable, refund)
    check_fields_and_types(data, None, updateable)

    # Handle refund revoke
    if 'revoked' in data:
        if refund.revoked == data['revoked']:
            raise exc.NothingHasChanged()
        refund.toggle_revoke(revoked=data['revoked'], admin_id=admin.id)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Updated refund.',
    }), 201
