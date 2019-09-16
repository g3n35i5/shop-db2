#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from sqlalchemy.exc import IntegrityError
from flask import jsonify
import shopdb.exceptions as exc
from shopdb.helpers.decorators import adminRequired
from shopdb.helpers.validators import check_fields_and_types, check_forbidden
from shopdb.helpers.utils import convert_minimal, json_body
from shopdb.api import app, db
from shopdb.models import Payoff


@app.route('/payoffs', methods=['GET'])
@adminRequired
def list_payoffs(admin):
    """
    Returns a list of all payoffs.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A list of all payoffs.
    """
    payoffs = Payoff.query.all()
    fields = ['id', 'timestamp', 'amount', 'comment', 'revoked', 'admin_id']
    return jsonify({'payoffs': convert_minimal(payoffs, fields)}), 200


@app.route('/payoffs/<int:id>', methods=['GET'])
@adminRequired
def get_payoff(admin, id):
    """
    Returns the payoff with the requested id.

    :param admin:          Is the administrator user, determined by
                           @adminRequired.
    :param id:             Is the payoff id.

    :return:               The requested payoff as JSON object.

    :raises EntryNotFound: If the payoff with this ID does not exist.
    """
    # Query the payoff
    res = Payoff.query.filter_by(id=id).first()
    # If it not exists, return an error
    if not res:
        raise exc.EntryNotFound()
    # Convert the payoff to a JSON friendly format
    fields = ['id', 'timestamp', 'amount', 'comment', 'revoked',
              'revokehistory']
    return jsonify({'payoff': convert_minimal(res, fields)[0]}), 200


@app.route('/payoffs', methods=['POST'])
@adminRequired
def create_payoff(admin):
    """
    Insert a new payoff.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.

    :return:                     A message that the creation was successful.

    :raises DataIsMissing:       If not all required data is available.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises InvalidAmount:       If amount is equal to zero.
    :raises CouldNotCreateEntry: If any other error occurs.
    """
    data = json_body()
    required = {'amount': int, 'comment': str}
    check_fields_and_types(data, required)

    # Check amount
    if data['amount'] <= 0:
        raise exc.InvalidAmount()

    # Create and insert payoff
    try:
        payoff = Payoff(**data)
        payoff.admin_id = admin.id
        db.session.add(payoff)
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created payoff.'}), 200


@app.route('/payoffs/<int:id>', methods=['PUT'])
@adminRequired
def update_payoff(admin, id):
    """
    Update the payoff with the given id.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the payoff id.

    :return:                     A message that the update was
                                 successful and a list of all updated fields.

    :raises EntryNotFound:       If the payoff with this ID does not exist.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid
                                 type.
    :raises NothingHasChanged:   If no change occurred after the update.
    :raises CouldNotUpdateEntry: If any other error occurs.
    """
    # Check payoff
    payoff = Payoff.query.filter_by(id=id).first()
    if not payoff:
        raise exc.EntryNotFound()

    data = json_body()

    if not data:
        raise exc.NothingHasChanged()

    updateable = {'revoked': bool}
    check_forbidden(data, updateable, payoff)
    check_fields_and_types(data, None, updateable)

    # Handle payoff revoke
    if 'revoked' in data:
        if payoff.revoked == data['revoked']:
            raise exc.NothingHasChanged()
        payoff.toggle_revoke(revoked=data['revoked'], admin_id=admin.id)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Updated payoff.',
    }), 201
