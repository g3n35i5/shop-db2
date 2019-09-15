#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import datetime
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from flask import jsonify, render_template, make_response
import pdfkit
import collections
import shopdb.exceptions as exc
from shopdb.helpers.stocktakings import _get_balance_between_stocktakings
from shopdb.api import (app, adminRequired, convert_minimal, db, check_fields_and_types, check_forbidden, json_body,
                        check_allowed_parameters, update_fields)
from shopdb.models import StocktakingCollection, Stocktaking, Product


@app.route('/stocktakingcollections/template', methods=['GET'])
@adminRequired
def get_stocktakingcollection_template(admin):
    """
    This route can be used to retrieve a template to print out for a
    stocktaking. It lists all the products that must be included in the
    stocktaking.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A rendered PDF file with all products for the stocktaking.
    """
    # Get a list of all products.
    products = (Product.query
                .filter(Product.active.is_(True))
                .filter(Product.countable.is_(True))
                .order_by(func.lower(Product.name))
                .all())

    # If no products exist that are active and countable, an exception must be
    # made.
    if not products:
        raise exc.EntryNotFound()

    # Render the template
    rendered = render_template('stocktakingcollections_template.html',
                               products=products)
    # Create a PDF file from the rendered template.
    pdf = pdfkit.from_string(rendered, False)
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=output.pdf'

    # Return the PDF file.
    return response


@app.route('/stocktakingcollections/balance', methods=['GET'])
@adminRequired
def get_balance_between_stocktakings(admin):
    """
    Returns the balance between two stocktakingcollections.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A dictionary containing all information about the balance
                  between the stocktakings.
    """
    allowed_params = {'start_id': int, 'end_id': int}
    args = check_allowed_parameters(allowed_params)
    start_id = args.get('start_id', None)
    end_id = args.get('end_id', None)

    # Check for all required arguments
    if not all([start_id, end_id]):
        raise exc.InvalidData()

    # Check the ids.
    if end_id <= start_id:
        raise exc.InvalidData()

    # Query the stocktakingcollections.
    start = StocktakingCollection.query.filter_by(id=start_id).first()
    end = StocktakingCollection.query.filter_by(id=end_id).first()

    # Return the balance.
    balance = _get_balance_between_stocktakings(start, end)
    return jsonify({'balance': balance}), 200


@app.route('/stocktakingcollections', methods=['GET'])
@adminRequired
def list_stocktakingcollections(admin):
    """
    Returns a list of all stocktakingcollections.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A list of all stocktakingcollections.
    """
    data = (StocktakingCollection.query
            .order_by(StocktakingCollection.timestamp)
            .all())
    fields = ['id', 'timestamp', 'admin_id', 'revoked']
    response = convert_minimal(data, fields)
    return jsonify({'stocktakingcollections': response}), 200


@app.route('/stocktakingcollections/<int:id>', methods=['GET'])
@adminRequired
def get_stocktakingcollections(admin, id):
    """
    Returns the stocktakingcollection with the requested id. In addition,
    all stocktakings that belong to this collection are returned.

    :param admin:          Is the administrator user,
                           determined by @adminRequired.
    :param id:             Is the stocktakingcollection id.

    :return:               The requested stocktakingcollection and all
                           related stocktakings JSON object.

    :raises EntryNotFound: If the stocktakingcollection with this ID does
                           not exist.
    """
    # Query the stocktakingcollection.
    collection = StocktakingCollection.query.filter_by(id=id).first()
    # If it does not exist, raise an exception.
    if not collection:
        raise exc.EntryNotFound()

    fields_collection = ['id', 'timestamp', 'admin_id', 'revoked',
                         'revokehistory']
    fields_stocktaking = ['id', 'product_id', 'count', 'collection_id']
    stocktakings = collection.stocktakings.all()

    result = convert_minimal(collection, fields_collection)[0]
    result['stocktakings'] = convert_minimal(stocktakings, fields_stocktaking)
    return jsonify({'stocktakingcollection': result}), 200


@app.route('/stocktakingcollections', methods=['POST'])
@adminRequired
def create_stocktakingcollections(admin):
    """
    Insert a new stocktakingcollection.

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
    required = {'stocktakings': list, 'timestamp': int}
    required_s = {'product_id': int, 'count': int}
    optional_s = {'set_inactive': bool}

    # Check all required fields
    check_fields_and_types(data, required)

    stocktakings = data['stocktakings']
    # Check for stocktakings in the collection
    if not stocktakings:
        raise exc.DataIsMissing()

    for stocktaking in stocktakings:
        product_id = stocktaking.get('product_id')
        product = Product.query.filter_by(id=product_id).first()
        if not product:
            raise exc.EntryNotFound()
        if not product.countable:
            raise exc.InvalidData()

    # Get all active product ids
    products = (Product.query
                .filter(Product.active.is_(True))
                .filter(Product.countable.is_(True))
                .all())
    active_ids = list(map(lambda p: p.id, products))
    data_product_ids = list(map(lambda d: d['product_id'], stocktakings))

    # Compare function
    def compare(x, y):
        return collections.Counter(x) == collections.Counter(y)

    # We need an entry for all active products. If some data is missing,
    # raise an exception
    if not compare(active_ids, data_product_ids):
        raise exc.DataIsMissing()

    # Check the timestamp
    try:
        timestamp = datetime.datetime.fromtimestamp(data['timestamp'])
        assert timestamp <= datetime.datetime.now()
    except (AssertionError, TypeError, ValueError, OSError, OverflowError):
        """
        AssertionError: The timestamp is after the current time.
        TypeError:      Invalid type for conversion.
        ValueError:     Timestamp is out of valid range.
        OSError:        Value exceeds the data type.
        OverflowError:  Timestamp out of range for platform time_t.
        """
        raise exc.InvalidData()
    # Create stocktakingcollection
    collection = StocktakingCollection(admin_id=admin.id, timestamp=timestamp)
    db.session.add(collection)
    db.session.flush()

    # Check for all required data and types
    for stocktaking in stocktakings:

        # Check all required fields
        check_fields_and_types(stocktaking, required_s, optional_s)

        # Get all fields
        product_id = stocktaking.get('product_id')
        count = stocktaking.get('count')
        set_inactive = stocktaking.get('set_inactive', False)

        # Check amount
        if count < 0:
            raise exc.InvalidAmount()

        # Does the product changes its active state?
        product = Product.query.filter_by(id=product_id).first()
        if set_inactive:
            if count == 0 and product.active:
                product.active = False
            else:
                raise exc.CouldNotUpdateEntry()

    # Create and insert stocktakingcollection
    try:
        for stocktaking in stocktakings:
            s = Stocktaking(
                collection_id=collection.id,
                product_id=stocktaking.get('product_id'),
                count=stocktaking.get('count'))
            db.session.add(s)
        db.session.commit()

    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created stocktakingcollection.'}), 201


@app.route('/stocktakingcollections/<int:id>', methods=['PUT'])
@adminRequired
def update_stocktakingcollection(admin, id):
    """
    Update the stocktakingcollection with the given id.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the stocktakingcollection id.

    :return:                     A message that the update was successful.

    :raises EntryNotFound:       If the stocktakingcollection with this ID
                                 does not exist.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid type.
    :raises NothingHasChanged:   If no change occurred after the update.
    :raises CouldNotUpdateEntry: If any other error occurs.
    """
    # Check StocktakingCollection
    collection = (StocktakingCollection.query.filter_by(id=id).first())
    if not collection:
        raise exc.EntryNotFound()

    data = json_body()

    if data == {}:
        raise exc.NothingHasChanged()

    updateable = {'revoked': bool}
    check_forbidden(data, updateable, collection)
    check_fields_and_types(data, None, updateable)

    updated_fields = []
    # Handle revoke
    if 'revoked' in data:
        if collection.revoked == data['revoked']:
            raise exc.NothingHasChanged()
        collection.toggle_revoke(revoked=data['revoked'], admin_id=admin.id)
        del data['revoked']
        updated_fields.append('revoked')

    # Handle all other fields
    updated_fields = update_fields(data, collection, updated_fields)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Updated stocktakingcollection.',
        'updated_fields': updated_fields
    }), 201


@app.route('/stocktakings/<int:id>', methods=['PUT'])
@adminRequired
def update_stocktaking(admin, id):
    """
    Update the stocktaking with the given id.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the stocktaking id.

    :return:                     A message that the update was successful
                                 and a list of all updated fields.

    :raises EntryNotFound:       If the stocktaking with this ID does not
                                 exist.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the
                                 request data.
    :raises InvalidType:         If one or more parameters have an invalid
                                 type.
    :raises NothingHasChanged:   If no change occurred after the update.
    :raises CouldNotUpdateEntry: If any other error occurs.
    """
    # Check Stocktaking
    stocktaking = Stocktaking.query.filter_by(id=id).first()
    if not stocktaking:
        raise exc.EntryNotFound()

    # Data validation
    data = json_body()
    updateable = {'count': int}
    check_forbidden(data, updateable, stocktaking)
    check_fields_and_types(data, None, updateable)

    updated_fields = []
    message = 'Updated stocktaking.'

    # Check count
    if 'count' in data:
        if data['count'] < 0:
            raise exc.InvalidAmount()

        if data['count'] == stocktaking.count:
            raise exc.NothingHasChanged()

    # Handle all other fields
    updated_fields = update_fields(data, stocktaking, updated_fields)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': message,
        'updated_fields': updated_fields
    }), 201
