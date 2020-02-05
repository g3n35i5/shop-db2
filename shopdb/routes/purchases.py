#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import exists
from flask import jsonify, request
import shopdb.exceptions as exc
from shopdb.helpers.decorators import adminOptional
from shopdb.helpers.validators import check_fields_and_types, check_forbidden, check_allowed_parameters
from shopdb.helpers.utils import convert_minimal, update_fields, json_body
from shopdb.helpers.query import QueryFromRequestParameters
from shopdb.api import app, db
from shopdb.models import Purchase, Product, User, Rank, PurchaseRevoke


@app.route('/purchases', methods=['GET'])
@adminOptional
def list_purchases(admin):
    """
    Returns a list of all purchases. If this route is called by an
    administrator, all information is returned. However, if it is called
    without further rights, a minimal version is returned.

    :param admin: Is the administrator user, determined by @adminOptional.

    :return:      A list of all purchases.
    """
    if admin is not None:
        fields = ['id', 'timestamp', 'user_id', 'product_id', 'productprice', 'amount', 'revoked', 'price']
    else:
        fields = ['id', 'timestamp', 'user_id', 'product_id', 'amount']

    query = QueryFromRequestParameters(Purchase, request.args, fields)
    if admin is None:
        query = query.filter(~exists().where(PurchaseRevoke.purchase_id == Purchase.id))

    result, content_range = query.result()
    response = jsonify(convert_minimal(result, fields))
    response.headers['Content-Range'] = content_range
    return response


@app.route('/purchases', methods=['POST'])
@adminOptional
def create_purchase(admin):
    """
    Insert a new purchase.

    :param admin:                Is the administrator user, determined by @adminOptional.

    :return:                     A message that the creation was successful.

    :raises DataIsMissing:       If not all required data is available.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises EntryNotFound:       If the user with this ID does not exist.
    :raises UserIsNotVerified:   If the user has not yet been verified.
    :raises EntryNotFound:       If the product with this ID does not exist.
    :raises EntryIsNotForSale:   If the product is not for sale.
    :raises EntryIsInactive:     If the product is inactive.
    :raises InvalidAmount:       If amount is less than or equal to zero.
    :raises InsufficientCredit:  If the credit balance of the user is not
                                 sufficient.
    :raises CouldNotCreateEntry: If any other error occurs.
    """
    data = json_body()
    required = {'user_id': int, 'product_id': int, 'amount': int}

    check_fields_and_types(data, required)

    # Check user
    user = User.query.filter_by(id=data['user_id']).first()
    if not user:
        raise exc.EntryNotFound()

    # Check if the user has been verified.
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    # Check if the user is inactive
    if not user.active:
        raise exc.UserIsInactive()

    # Check product
    product = Product.query.filter_by(id=data['product_id']).first()
    if not product:
        raise exc.EntryNotFound()
    if not admin and not product.active:
        raise exc.EntryIsInactive()

    # Check weather the product is for sale
    if any(map(lambda tag: not tag.is_for_sale, product.tags)):
        raise exc.EntryIsNotForSale()

    # Check amount
    if data['amount'] <= 0:
        raise exc.InvalidAmount()

    # If the purchase is made by an administrator, the credit limit
    # may be exceeded.
    if not admin:
        limit = Rank.query.filter_by(id=user.rank_id).first().debt_limit
        current_credit = user.credit
        future_credit = current_credit - (product.price * data['amount'])
        if future_credit < limit:
            raise exc.InsufficientCredit()

    try:
        purchase = Purchase(**data)
        db.session.add(purchase)
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Purchase created.'}), 200


@app.route('/purchases/<int:id>', methods=['GET'])
def get_purchase(id):
    """
    Returns the purchase with the requested id.

    :param id:             Is the purchase id.

    :return:               The requested purchase as JSON object.

    :raises EntryNotFound: If the purchase with this ID does not exist.
    """
    purchase = Purchase.query.filter_by(id=id).first()
    if not purchase:
        raise exc.EntryNotFound()
    fields = ['id', 'timestamp', 'user_id', 'product_id', 'amount', 'price',
              'productprice', 'revoked', 'revokehistory']
    return jsonify(convert_minimal(purchase, fields)[0]), 200


@app.route('/purchases/<int:id>', methods=['PUT'])
def update_purchase(id):
    """
    Update the purchase with the given id.

    :param id:                   Is the purchase id.

    :return:                     A message that the update was
                                 successful and a list of all updated fields.

    :raises EntryNotFound:       If the purchase with this ID does not exist.
    :raises EntryNotRevocable:   An attempt is made to revoked a purchase
                                 whose product is not revocable.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid
                                 type.
    :raises NothingHasChanged:   If no change occurred after the update.
    :raises CouldNotUpdateEntry: If any other error occurs.
    """
    # Check purchase
    purchase = Purchase.query.filter_by(id=id).first()
    if not purchase:
        raise exc.EntryNotFound()

    # Query the product
    product = Product.query.filter_by(id=purchase.product_id).first()

    data = json_body()
    updateable = {'revoked': bool, 'amount': int}
    check_forbidden(data, updateable, purchase)
    check_fields_and_types(data, None, updateable)

    updated_fields = []

    # Handle purchase revoke
    if 'revoked' in data:
        # In case that the product is not revocable, an exception must be made.
        if not product.revocable:
            raise exc.EntryNotRevocable()
        if purchase.revoked == data['revoked']:
            raise exc.NothingHasChanged()
        purchase.toggle_revoke(revoked=data['revoked'])
        updated_fields.append('revoked')
        del data['revoked']

    # Handle all other fields
    updated_fields = update_fields(data, purchase, updated=updated_fields)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Updated purchase.',
        'updated_fields': updated_fields
    }), 201
