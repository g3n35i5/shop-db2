#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import datetime
from sqlalchemy.exc import IntegrityError
from flask import jsonify
import shopdb.exceptions as exc
from shopdb.helpers.decorators import adminRequired
from shopdb.helpers.validators import check_fields_and_types, check_forbidden
from shopdb.api import (app, convert_minimal, db, json_body, update_fields)
from shopdb.models import Replenishment, ReplenishmentCollection, Product


@app.route('/replenishmentcollections', methods=['GET'])
@adminRequired
def list_replenishmentcollections(admin):
    """
    Returns a list of all replenishmentcollections.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A list of all replenishmentcollections.
    """
    data = ReplenishmentCollection.query.all()
    fields = ['id', 'timestamp', 'admin_id', 'price', 'revoked', 'comment']
    response = convert_minimal(data, fields)
    return jsonify({'replenishmentcollections': response}), 200


@app.route('/replenishmentcollections/<int:id>', methods=['GET'])
@adminRequired
def get_replenishmentcollection(admin, id):
    """
    Returns the replenishmentcollection with the requested id. In addition,
    all replenishments that belong to this collection are returned.

    :param admin:          Is the administrator user,
                           determined by @adminRequired.
    :param id:             Is the replenishmentcollection id.

    :return:               The requested replenishmentcollection and all
                           related replenishments JSON object.

    :raises EntryNotFound: If the replenishmentcollection with this ID does
                           not exist.
    """
    # Query the replenishmentcollection.
    replcoll = ReplenishmentCollection.query.filter_by(id=id).first()
    # If it does not exist, raise an exception.
    if not replcoll:
        raise exc.EntryNotFound()

    fields_replcoll = ['id', 'timestamp', 'admin_id', 'price', 'revoked',
                       'revokehistory', 'comment']
    fields_repl = ['id', 'replcoll_id', 'product_id', 'amount',
                   'total_price', 'revoked']
    repls = replcoll.replenishments.all()

    result = convert_minimal(replcoll, fields_replcoll)[0]
    result['replenishments'] = convert_minimal(repls, fields_repl)
    return jsonify({'replenishmentcollection': result}), 200


@app.route('/replenishmentcollections', methods=['POST'])
@adminRequired
def create_replenishmentcollection(admin):
    """
    Insert a new replenishmentcollection.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.

    :return:                     A message that the creation was successful.

    :raises DataIsMissing:       If not all required data is available.
    :raises ForbiddenField :     If a forbidden field is in the data.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises EntryNotFound:       If the product with with the id of any
                                 replenishment does not exist.
    :raises InvalidAmount:       If amount of any replenishment is less than
                                 or equal to zero.
    :raises CouldNotCreateEntry: If any other error occurs.
    """
    data = json_body()
    required = {'replenishments': list, 'comment': str}
    required_repl = {'product_id': int, 'amount': int, 'total_price': int}

    # Check all required fields
    check_fields_and_types(data, required)

    replenishments = data['replenishments']
    # Check for the replenishments in the collection
    if not replenishments:
        raise exc.DataIsMissing()

    for repl in replenishments:

        # Check all required fields
        check_fields_and_types(repl, required_repl)

        product_id = repl.get('product_id')
        amount = repl.get('amount')

        # Check amount
        if amount <= 0:
            raise exc.InvalidAmount()
        # Check product
        product = Product.query.filter_by(id=product_id).first()
        if not product:
            raise exc.EntryNotFound()

        # If the product has been marked as inactive, it will now be marked as
        # active again.
        if not product.active:
            product.active = True

    # Create and insert replenishmentcollection
    try:
        collection = ReplenishmentCollection(admin_id=admin.id,
                                             comment=data['comment'],
                                             revoked=False)
        db.session.add(collection)
        db.session.flush()

        for repl in replenishments:
            rep = Replenishment(replcoll_id=collection.id, **repl)
            db.session.add(rep)
        db.session.commit()

    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created replenishmentcollection.'}), 201


@app.route('/replenishmentcollections/<int:id>', methods=['PUT'])
@adminRequired
def update_replenishmentcollection(admin, id):
    """
    Update the replenishmentcollection with the given id.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the replenishmentcollection id.

    :return:                     A message that the update was successful.

    :raises EntryNotFound:       If the replenishmentcollection with this ID
                                 does not exist.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid type.
    :raises NothingHasChanged:   If no change occurred after the update.
    :raises CouldNotUpdateEntry: If any other error occurs.
    :raises EntryNotRevocable:   If the replenishmentcollections was revoked by
                                 by replenishment_update, because all
                                 replenishments are revoked, the revoked field
                                 can not be set to true.
    """
    # Check ReplenishmentCollection
    replcoll = (ReplenishmentCollection.query.filter_by(id=id).first())
    if not replcoll:
        raise exc.EntryNotFound()
    # Which replenishments are not revoked?
    repls = replcoll.replenishments.filter_by(revoked=False).all()

    data = json_body()

    if data == {}:
        raise exc.NothingHasChanged()

    updateable = {'revoked': bool, 'comment': str, 'timestamp': int}
    check_forbidden(data, updateable, replcoll)
    check_fields_and_types(data, None, updateable)

    updated_fields = []
    # Handle replenishmentcollection revoke
    if 'revoked' in data:
        if replcoll.revoked == data['revoked']:
            raise exc.NothingHasChanged()
        # Check if the revoke was caused through the replenishment_update and
        # therefor cant be changed
        if not data['revoked'] and not repls:
            raise exc.EntryNotRevocable()
        replcoll.toggle_revoke(revoked=data['revoked'], admin_id=admin.id)
        del data['revoked']
        updated_fields.append('revoked')

    # Handle new timestamp
    if 'timestamp' in data:
        try:
            timestamp = datetime.datetime.fromtimestamp(data['timestamp'])
            assert timestamp <= datetime.datetime.now()
            replcoll.timestamp = timestamp
            updated_fields.append('revoked')
        except (AssertionError, TypeError, ValueError, OSError, OverflowError):
            """
            AssertionError: The timestamp lies in the future.
            TypeError:      Invalid type for conversion.
            ValueError:     Timestamp is out of valid range.
            OSError:        Value exceeds the data type.
            OverflowError:  Timestamp out of range for platform time_t.
            """
            raise exc.InvalidData()
        del data['timestamp']

    # Handle all other fields
    updated_fields = update_fields(data, replcoll, updated_fields)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Updated replenishmentcollection.',
        'updated_fields': updated_fields
    }), 201


@app.route('/replenishments/<int:id>', methods=['PUT'])
@adminRequired
def update_replenishment(admin, id):
    """
    Update the replenishment with the given id.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the replenishment id.

    :return:                     A message that the update was successful
                                 and a list of all updated fields.

    :raises EntryNotFound:       If the replenishment with this ID does not
                                 exist.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the
                                 request data.
    :raises InvalidType:         If one or more parameters have an invalid
                                 type.
    :raises NothingHasChanged:   If no change occurred after the update.
    :raises CouldNotUpdateEntry: If any other error occurs.
    """
    # Check Replenishment
    repl = Replenishment.query.filter_by(id=id).first()
    if not repl:
        raise exc.EntryNotFound()

    # Get the corresponding ReplenishmentCollection
    replcoll = (ReplenishmentCollection.query.filter_by(id=repl.replcoll_id)
                .first())
    # Get all not revoked replenishments corresponding to the
    # replenishmentcollection before changes are made
    repls_nr = replcoll.replenishments.filter_by(revoked=False).all()

    # Data validation
    data = json_body()
    updateable = {'revoked': bool, 'amount': int, 'total_price': int}
    check_forbidden(data, updateable, repl)
    check_fields_and_types(data, None, updateable)

    updated_fields = []
    message = 'Updated replenishment.'

    # Handle replenishment revoke
    if 'revoked' in data:
        if repl.revoked == data['revoked']:
            raise exc.NothingHasChanged()
        if not data['revoked'] and not repls_nr:
            replcoll.toggle_revoke(revoked=False, admin_id=admin.id)
            message = message + (' Rerevoked ReplenishmentCollection ID: {}'.format(replcoll.id))
        repl.toggle_revoke(revoked=data['revoked'], admin_id=admin.id)
        del data['revoked']
        updated_fields.append('revoked')

    # Handle all other fields
    updated_fields = update_fields(data, repl, updated_fields)

    # Check if ReplenishmentCollection still has unrevoked Replenishments
    repls = replcoll.replenishments.filter_by(revoked=False).all()
    if not repls and not replcoll.revoked:
        message = message + (' Revoked ReplenishmentCollection ID: {}'
                             .format(replcoll.id))
        replcoll.toggle_revoke(revoked=True, admin_id=admin.id)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': message,
        'updated_fields': updated_fields
    }), 201
