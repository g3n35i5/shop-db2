#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from sqlalchemy.exc import IntegrityError
from flask import jsonify, request
import shopdb.exceptions as exc
from shopdb.helpers.decorators import adminRequired
from shopdb.helpers.validators import check_fields_and_types, check_forbidden
from shopdb.helpers.utils import convert_minimal, json_body
from shopdb.helpers.query import QueryFromRequestParameters
from shopdb.api import app, db
from shopdb.models import Turnover


@app.route('/turnovers', methods=['GET'])
@adminRequired
def list_turnovers(admin):
    """
    Returns a list of all turnovers.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A list of all turnovers.
    """
    fields = ['id', 'timestamp', 'amount', 'comment', 'revoked', 'admin_id']
    query = QueryFromRequestParameters(Turnover, request.args, fields)
    result, content_range = query.result()
    response = jsonify(convert_minimal(result, fields))
    response.headers['Content-Range'] = content_range
    return response


@app.route('/turnovers', methods=['POST'])
@adminRequired
def create_turnover(admin):
    """
    Insert a new turnover.

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
    if data['amount'] == 0:
        raise exc.InvalidAmount()

    # Create and insert turnover
    try:
        turnover = Turnover(**data)
        turnover.admin_id = admin.id
        db.session.add(turnover)
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created turnover.'}), 200


@app.route('/turnovers/<int:id>', methods=['GET'])
def get_turnover(id):
    """
    Returns the turnover with the requested id.

    :param id:             Is the turnover id.

    :return:               The requested turnover as JSON object.

    :raises EntryNotFound: If the turnover with this ID does not exist.
    """
    # Query the turnover
    res = Turnover.query.filter_by(id=id).first()
    # If it not exists, return an error
    if not res:
        raise exc.EntryNotFound()
    # Convert the turnover to a JSON friendly format
    fields = ['id', 'timestamp', 'amount', 'comment', 'revoked',
              'revokehistory']
    return jsonify(convert_minimal(res, fields)[0]), 200


@app.route('/turnovers/<int:id>', methods=['PUT'])
@adminRequired
def update_turnover(admin, id):
    """
    Update the turnover with the given id.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the turnover id.

    :return:                     A message that the update was
                                 successful and a list of all updated fields.

    :raises EntryNotFound:       If the turnover with this ID does not exist.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid type.
    :raises NothingHasChanged:   If no change occurred after the update.
    :raises CouldNotUpdateEntry: If any other error occurs.
    """
    # Check turnover
    turnover = Turnover.query.filter_by(id=id).first()
    if not turnover:
        raise exc.EntryNotFound()

    data = json_body()

    if not data:
        raise exc.NothingHasChanged()

    updateable = {'revoked': bool}
    check_forbidden(data, updateable, turnover)
    check_fields_and_types(data, None, updateable)

    # Handle turnover revoke
    if 'revoked' in data:
        if turnover.revoked == data['revoked']:
            raise exc.NothingHasChanged()
        turnover.toggle_revoke(revoked=data['revoked'], admin_id=admin.id)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Updated turnover.',
    }), 201
