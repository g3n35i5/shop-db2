#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from sqlalchemy.exc import IntegrityError
from flask import jsonify, request
import shopdb.exceptions as exc
from shopdb.helpers.decorators import adminRequired, adminOptional
from shopdb.helpers.validators import check_fields_and_types, check_forbidden
from shopdb.helpers.utils import update_fields, convert_minimal, json_body
from shopdb.api import app, db
import shopdb.helpers.products as product_helpers
from shopdb.models import Product, Tag, Upload


@app.route('/products', methods=['GET'])
@adminOptional
def list_products(admin):
    """
    Returns a list of all products.

    :param admin: Is the administrator user, determined by @adminOptional.

    :return:      A list of all products
    """
    result = Product.query.all()
    fields = ['id', 'name', 'price', 'barcode', 'active', 'countable',
              'revocable', 'imagename', 'tags', 'creation_date']
    products = convert_minimal(result, fields)

    for product in products:
        product['tags'] = [t.id for t in product['tags']]
    return jsonify(products), 200


@app.route('/products', methods=['POST'])
@adminRequired
def create_product(admin):
    """
    Route to create a new product.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.

    :return:                     A message that the creation was successful.

    :raises DataIsMissing:       If one or more fields are missing to create
                                 the product.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid
                                 type.
    :raises EntryAlreadyExists:  If a product with this name already exists.
    :raises EntryAlreadyExists:  If the barcode already exists.
    :raises CouldNotCreateEntry: If the new product cannot be added to the
                                 database.
    """
    data = json_body()
    required = {'name': str, 'price': int, 'tags': list}
    optional = {
        'barcode': str, 'active': bool, 'countable': bool,
        'revocable': bool, 'imagename': str
    }

    # Check all required fields
    check_fields_and_types(data, required, optional)

    # Check if a product with this name already exists
    if Product.query.filter_by(name=data['name']).first():
        raise exc.EntryAlreadyExists()

    # Check if a product with this barcode already exists
    if 'barcode' in data:
        if Product.query.filter_by(barcode=data['barcode']).first():
            raise exc.EntryAlreadyExists()

    # Check the product tags
    tags = data['tags']
    for tag_id in tags:
        if not isinstance(tag_id, int):
            raise exc.WrongType
        tag = Tag.query.filter_by(id=tag_id).first()
        if not tag:
            raise exc.EntryNotFound

    del data['tags']

    # Save the price and delete it from the data dictionary
    price = int(data['price'])
    del data['price']

    try:
        product = Product(**data)
        product.created_by = admin.id
        db.session.add(product)
        db.session.flush()
        product.set_price(price=price, admin_id=admin.id)
        for tag_id in tags:
            tag = Tag.query.filter_by(id=tag_id).first()
            product.tags.append(tag)

        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created Product.'}), 201


@app.route('/products/<int:id>', methods=['GET'])
@adminOptional
def get_product(admin, id):
    """
    Returns the product with the requested id.

    :param admin:               Is the administrator user, determined by
                                @adminOptional.
    :param id:                  Is the product id.

    :return:                    The requested product as JSON object.

    :raises EntryNotFound:      If the product with this ID does not exist.
    :raises UnauthorizedAccess: If the product is inactive and the request
                                does not come from an administrator.
    """
    product = Product.query.filter(Product.id == id).first()
    if not product:
        raise exc.EntryNotFound()

    if not (product.active or admin):
        fields = ['id', 'name', 'barcode', 'active', 'imagename',
                  'tags', 'creation_date']
    else:
        fields = ['id', 'name', 'price', 'barcode', 'active', 'countable',
                  'revocable', 'imagename', 'tags', 'creation_date']

    # Convert the product to a dictionary
    product = convert_minimal(product, fields)[0]

    # Convert the product tags
    product['tags'] = [t.id for t in product['tags']]

    return jsonify(product), 200


@app.route('/products/<int:id>/stock', methods=['GET'])
def get_product_stock(id):
    """
    Returns the theoretical stock level of a product.

    The theoretical stock level of a product is the result of the number
    determined in the last stocktaking minus the number of purchases
    that were not revoked since then.

    If the requested product is not countable, None will be returned.

    :param id:                  Is the product id.

    :return:                    The theoretical stock level

    :raises EntryNotFound:      If the product with this ID does not exist.
    """

    # Check, whether the requested product exists
    product = Product.query.filter(Product.id == id).first()
    if not product:
        raise exc.EntryNotFound()

    # If the product is not countable, return None
    if not product.countable:
        return jsonify(None), 200

    # Get the theoretical stock level
    theoretical_stock = product_helpers.get_theoretical_stock_of_product(id)

    return jsonify(theoretical_stock), 200


@app.route('/products/<int:id>/pricehistory', methods=['GET'])
@adminRequired
def get_product_pricehistory(admin, id):
    """
    Returns the pricehistory of the product with the given id. If only want to
    query a part of the history in a range there are optional request arguments:
    - start_date:          Is the unix timestamp of the start date.
    - end_date:            Is the unix timestamp of the end date.

    :param admin:          Is the administrator user, determined by
                           @adminRequired.
    :param id:             Is the product id.

    :raises EntryNotFound: If the product does not exist.
    :raises WrongType:     If the request args are invalid.

    :return:               The pricehistory of the product.
    """

    # Check, whether the product exists.
    product = Product.query.filter(Product.id == id).first()
    if not product:
        raise exc.EntryNotFound()

    # Get the (optional) time range parameters
    try:
        start = request.args.get('start_date')
        if start:
            start = int(start)
        end = request.args.get('end_date')
        if end:
            end = int(end)
    except (TypeError, ValueError):
        raise exc.WrongType()

    # Check whether start lies before end date
    if start and end:
        if not start <= end:
            raise exc.InvalidData()

    history = product.get_pricehistory(start, end)

    return jsonify(history), 200


@app.route('/products/<int:id>', methods=['PUT'])
@adminRequired
def update_product(admin, id):
    """
    Update the product with the given id.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the product id.

    :return:                     A message that the update was
                                 successful and a list of all updated fields.

    :raises EntryNotFound:       If the product with this ID does not exist.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid type.
    :raises EntryNotFound:       If the image is to be changed but no image
                                 with this name exists.
    :raises CouldNotUpdateEntry: If any other error occurs.
    """
    data = json_body()

    # Check, if the product exists.
    product = Product.query.filter_by(id=id).first()
    if not product:
        raise exc.EntryNotFound()

    optional = {
        'name': str, 'price': int, 'barcode': str,
        'imagename': str, 'countable': bool, 'revocable': bool
    }

    # Check forbidden fields
    check_forbidden(data, optional, product)
    # Check types
    check_fields_and_types(data, None, optional)

    updated_fields = []

    # Check for price change
    if 'price' in data:
        price = int(data['price'])
        del data['price']
        if price != product.price:
            product.set_price(price=price, admin_id=admin.id)
            updated_fields.append('price')

    # Check for barcode change
    if 'barcode' in data:
        if Product.query.filter_by(barcode=data['barcode']).first():
            raise exc.EntryAlreadyExists()

    # Check for image change.
    if 'imagename' in data:
        imagename = data['imagename']
        del data['imagename']
        if imagename != product.imagename:
            upload = Upload.query.filter_by(filename=imagename).first()
            if not upload:
                raise exc.EntryNotFound()

            product.image_upload_id = upload.id
            updated_fields.append('imagename')

    # Update all other fields
    updated_fields = update_fields(data, product, updated=updated_fields)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Updated product.',
        'updated_fields': updated_fields
    }), 201
