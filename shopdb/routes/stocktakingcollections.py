#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import collections
import datetime

try:
    import pdfkit
except ImportError:
    pdfkit = None
    pass

from flask import jsonify, render_template, make_response, request
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

import shopdb.exceptions as exc
import shopdb.helpers.products as product_helpers
from shopdb.api import app, db
from shopdb.helpers.decorators import adminRequired
from shopdb.helpers.query import QueryFromRequestParameters
from shopdb.helpers.stocktakings import _get_balance_between_stocktakings
from shopdb.helpers.utils import convert_minimal, json_body
from shopdb.helpers.updater import generic_update
from shopdb.helpers.validators import check_fields_and_types, check_allowed_parameters
from shopdb.models import StocktakingCollection, Stocktaking, Product


@app.route('/stocktakingcollections/template', methods=['GET'])
def get_stocktakingcollection_template():
    """
    This route can be used to retrieve a template to print out for a
    stocktaking. It lists all the products that must be included in the stocktaking.

    :return:      A rendered PDF file with all products for the stocktaking.
    """
    # Check if pdfkit is available
    if pdfkit is None:
        return jsonify({'message': 'Not available'}), 503

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

    rows = []
    for product in products:
        product_name = product.name
        theoretical_stock = product_helpers.get_theoretical_stock_of_product(product.id)
        rows.append({'product_name': product_name, 'theoretical_stock': theoretical_stock})

    # Render the template
    rendered = render_template('stocktakingcollections_template.html', rows=rows)
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
    return jsonify(balance), 200


@app.route('/stocktakingcollections', methods=['GET'])
@adminRequired
def list_stocktakingcollections(admin):
    """
    Returns a list of all stocktakingcollections.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A list of all stocktakingcollections.
    """
    fields = ['id', 'timestamp', 'admin_id', 'revoked']
    query = QueryFromRequestParameters(StocktakingCollection, request.args, fields)
    result, content_range = query.result()
    response = jsonify(convert_minimal(result, fields))
    response.headers['Content-Range'] = content_range
    return response


@app.route('/stocktakingcollections/<int:collection_id>', methods=['GET'])
@adminRequired
def get_stocktakingcollections(admin, collection_id):
    """
    Returns the stocktakingcollection with the requested id. In addition,
    all stocktakings that belong to this collection are returned.

    :param admin:          Is the administrator user,
                           determined by @adminRequired.
    :param collection_id:  Is the stocktakingcollection id.

    :return:               The requested stocktakingcollection and all
                           related stocktakings JSON object.

    :raises EntryNotFound: If the stocktakingcollection with this ID does
                           not exist.
    """
    # Query the stocktakingcollection.
    collection = StocktakingCollection.query.filter_by(id=collection_id).first()
    # If it does not exist, raise an exception.
    if not collection:
        raise exc.EntryNotFound()

    fields_collection = ['id', 'timestamp', 'admin_id', 'revoked',
                         'revokehistory']
    fields_stocktaking = ['id', 'product_id', 'count', 'collection_id']
    stocktakings = collection.stocktakings.all()

    result = convert_minimal(collection, fields_collection)[0]
    result['stocktakings'] = convert_minimal(stocktakings, fields_stocktaking)
    return jsonify(result), 200


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
    optional_s = {'keep_active': bool}

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
        keep_active = stocktaking.get('keep_active', False)

        # Check amount
        if count < 0:
            raise exc.InvalidAmount()

        # Does the product changes its active state?
        product = Product.query.filter_by(id=product_id).first()
        if count == 0 and keep_active is False:
            product.active = False

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


@app.route('/stocktakingcollections/<int:collection_id>', methods=['PUT'])
@adminRequired
def update_stocktakingcollection(admin, collection_id):
    """
    Update the stocktakingcollection with the given id.

    :param admin:         Is the administrator user, determined by @adminRequired.
    :param collection_id: Is the stocktakingcollection id.

    :return:              A message that the update was successful and a list of all updated fields.
    """
    return generic_update(StocktakingCollection, collection_id, json_body(), admin)


@app.route('/stocktakings/<int:stocktaking_id>', methods=['PUT'])
@adminRequired
def update_stocktaking(admin, stocktaking_id):
    """
    Update the stocktaking with the given id.

    :param admin:          Is the administrator user, determined by @adminRequired.
    :param stocktaking_id: Is the stocktaking id.

    :return:               A message that the update was successful and a list of all updated fields.
    """
    return generic_update(Stocktaking, stocktaking_id, json_body(), admin)
