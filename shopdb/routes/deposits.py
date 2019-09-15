#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from sqlalchemy.exc import IntegrityError
from flask import jsonify
import shopdb.exceptions as exc
from shopdb.api import (app, convert_minimal, db, json_body, insert_deposit)
from shopdb.models import Deposit
from shopdb.helpers.decorators import adminRequired
from shopdb.helpers.validators import check_fields_and_types, check_forbidden


@app.route('/deposits', methods=['GET'])
@adminRequired
def list_deposits(admin):
    """
    Returns a list of all deposits.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A list of all deposits.
    """
    deposits = Deposit.query.all()
    fields = ['id', 'timestamp', 'user_id', 'amount', 'comment', 'revoked',
              'admin_id']
    return jsonify({'deposits': convert_minimal(deposits, fields)}), 200


@app.route('/deposits', methods=['POST'])
@adminRequired
def create_deposit(admin):
    """
    Insert a new deposit.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.

    :return:                     A message that the creation was successful.

    :raises DataIsMissing:       If not all required data is available.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises EntryNotFound:       If the user with this ID does not exist.
    :raises UserIsNotVerified:   If the user has not yet been verified.
    :raises InvalidAmount:       If amount is equal to zero.
    :raises CouldNotCreateEntry: If any other error occurs.
    """
    data = json_body()

    # Use the insert deposit helper function to create the deposit entry.
    insert_deposit(data, admin)

    # Try to commit the deposit.
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created deposit.'}), 200


@app.route('/deposits/batch', methods=['POST'])
@adminRequired
def create_batch_deposit(admin):
    """
    Insert a new batch deposit.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.

    :return:                     A message that the creation was successful.

    :raises DataIsMissing:       If not all required data is available.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises EntryNotFound:       If any user cannot be found.
    :raises UserIsNotVerified:   If any user is not verified.
    :raises InvalidAmount:       If amount is equal to zero.
    :raises CouldNotCreateEntry: If any other error occurs.
    """
    data = json_body()
    required = {'user_ids': list, 'amount': int, 'comment': str}
    check_fields_and_types(data, required)

    # Call the insert deposit helper function for each user.
    for user_id in data['user_ids']:
        data = {
            'user_id': user_id,
            'comment': data['comment'],
            'amount': data['amount']}
        insert_deposit(data, admin)

    # Try to commit the changes.
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created batch deposit.'}), 200


@app.route('/deposits/<int:id>', methods=['GET'])
def get_deposit(id):
    """
    Returns the deposit with the requested id.

    :param id:             Is the deposit id.

    :return:               The requested deposit as JSON object.

    :raises EntryNotFound: If the deposit with this ID does not exist.
    """
    # Query the deposit
    res = Deposit.query.filter_by(id=id).first()
    # If it not exists, return an error
    if not res:
        raise exc.EntryNotFound()
    # Convert the deposit to a JSON friendly format
    fields = ['id', 'timestamp', 'user_id', 'amount', 'comment', 'revoked',
              'revokehistory']
    return jsonify({'deposit': convert_minimal(res, fields)[0]}), 200


@app.route('/deposits/<int:id>', methods=['PUT'])
@adminRequired
def update_deposit(admin, id):
    """
    Update the deposit with the given id.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the deposit id.

    :return:                     A message that the update was
                                 successful and a list of all updated fields.

    :raises EntryNotFound:       If the deposit with this ID does not exist.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid type.
    :raises NothingHasChanged:   If no change occurred after the update.
    :raises CouldNotUpdateEntry: If any other error occurs.
    """
    # Check deposit
    deposit = Deposit.query.filter_by(id=id).first()
    if not deposit:
        raise exc.EntryNotFound()

    data = json_body()

    if not data:
        raise exc.NothingHasChanged()

    updateable = {'revoked': bool}
    check_forbidden(data, updateable, deposit)
    check_fields_and_types(data, None, updateable)

    # Handle deposit revoke
    if 'revoked' in data:
        if deposit.revoked == data['revoked']:
            raise exc.NothingHasChanged()
        deposit.toggle_revoke(revoked=data['revoked'], admin_id=admin.id)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Updated deposit.',
    }), 201
