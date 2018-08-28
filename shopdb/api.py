#!/usr/bin/env python3

from shopdb.models import *
import shopdb.exceptions as exc
from flask import (Flask, request, g, make_response, jsonify)
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import jwt
import sqlite3
import sqlalchemy
from sqlalchemy.sql import exists
from sqlalchemy.exc import *
from functools import wraps
import datetime
import configuration as config
app = Flask(__name__)

# Default app settings (to suppress unittest warnings) will be overwritten.
app.config.from_object(config.BaseConfig)
db.init_app(app)
bcrypt = Bcrypt(app)


def convert_minimal(data, fields):
    '''This function returns only the required attributes of all objects in
       given list.'''
    out = []
    if not isinstance(data, list):
        data = [data]

    for item in data:
        element = {}
        for field in fields:
            element[field] = getattr(item, field)

        out.append(element)

    if len(out) > 1:
        return out
    return out[0]


def adminRequired(f):
    '''This function checks whether a valid token is contained in the request.
       If this is not the case, or the user has no admin rights, the request
       will be blocked.'''
    @wraps(f)
    def decorated(*args, **kwargs):
        # Does the request heder contain a token?
        try:
            token = request.headers['token']
        except KeyError:
            raise exc.UnauthorizedAccess()

        # Is the token valid?
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
        except jwt.exceptions.DecodeError:
            raise exc.TokenIsInvalid()
        except jwt.ExpiredSignatureError:
            raise exc.TokenHasExpired()

        # If there is no admin object in the token and does the user does have
        # admin rights?
        try:
            admin_id = data['user']['id']
            admin = User.query.filter(User.id == admin_id).first()
            assert admin.is_admin is True
        except KeyError:
            raise exc.TokenIsInvalid()
        except AssertionError:
            raise exc.UnauthorizedAccess()

        # At this point it was verified that the request comes from an
        # admin and the request is executed. In addition, the user is
        # forwarded to the following function so that the administrator
        # responsible for any changes in the database can be traced.
        return f(admin, *args, **kwargs)
    return decorated


def adminOptional(f):
    '''This function checks whether a valid token is contained in the request.
       If this is not the case, or the user has no admin rights, the following
       function returns only a part of the available data.'''
    @wraps(f)
    def decorated(*args, **kwargs):
        # Does the request heder contain a token?
        try:
            token = request.headers['token']
        except KeyError:
            return f(None, *args, **kwargs)

        # Is the token valid?
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
        except jwt.exceptions.DecodeError:
            raise exc.TokenIsInvalid()
        except jwt.ExpiredSignatureError:
            raise exc.TokenHasExpired()

        # If there is no admin object in the token and does the user does have
        # admin rights?
        try:
            admin_id = data['user']['id']
            admin = User.query.filter(User.id == admin_id).first()
            assert admin.is_admin is True
        except KeyError:
            raise exc.TokenIsInvalid()
        except AssertionError:
            return f(None, *args, **kwargs)

        # At this point it was verified that the request comes from an
        # admin and the request is executed. In addition, the user is
        # forwarded to the following function so that the administrator
        # responsible for any changes in the database can be traced.
        return f(admin, *args, **kwargs)
    return decorated


@app.errorhandler(Exception)
def handle_error(error):
    '''This wrapper catches all exceptions and, if possible, returns a user
       friendly response. Otherwise, it will raise the error'''
    # Perform a rollback. All changes that have not yet been committed are
    # thus reset.
    db.session.rollback()
    # As long as the application is in debug mode, all exceptions
    # should be output immediately.
    if app.config['DEBUG']:  # pragma: no cover
        raise error
    # Create, if possible, a user friendly response.
    if all(hasattr(error, item) for item in ['type', 'message', 'code']):
        return jsonify(result=error.type, message=error.message), error.code
    else:   # pragma: no cover
        raise error
    # If for some reason no exception has been raised yet, this is done now.
    raise error  # pragma: no cover


def json_body():
    jb = request.get_json()
    if jb is None:
        raise exc.InvalidJSON()
    return jb


# Login route ################################################################
@app.route('/login', methods=['POST'])
def login():
    '''Authenticate a registered user'''
    data = json_body()
    user = None
    # Check if the username is included in the request.
    if 'username' in data and data['username'] is not '':
        user = User.query.filter_by(username=str(data['username'])).first()
        if not user:
            raise exc.InvalidCredentials()

    # Check, if the username is not available, if an email address is
    # available in the request.
    elif 'email' in data and data['email'] is not '':
        user = User.query.filter_by(email=str(data['email'])).first()
        if not user:
            raise exc.InvalidCredentials()

    # If no user with this data exists or there is no password in the
    # request, cancel the authentication.
    if not user or 'password' not in data:
        raise exc.DataIsMissing()

    # Check if the user has already been verified.
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    # Check if the password matches the user's password.
    if not bcrypt.check_password_hash(user.password, str(data['password'])):
        raise exc.InvalidCredentials()

    # Create a dictionary object of the user.
    d_user = user.to_dict()

    # Create a token.
    exp = datetime.datetime.now() + datetime.timedelta(minutes=15)
    token = jwt.encode({'user': d_user, 'exp': exp}, app.config['SECRET_KEY'])

    # Return the result.
    return jsonify({'result': True, 'token': token.decode('UTF-8')}), 200


# Register route #############################################################
@app.route('/register', methods=['POST'])
def register():
    '''Register a new user'''
    data = json_body()
    required = ['firstname', 'lastname', 'username', 'email',
                'password', 'repeat_password']

    # Check whether all required values are available.
    if any(item not in data for item in required):
        raise exc.DataIsMissing()

    # Check all values for their type.
    try:
        for item in required:
            assert isinstance(data[item], str)
    except AssertionError:
        raise exc.WrongType()

    # Check if the passwords match.
    if data['password'] != data['repeat_password']:
        raise exc.PasswordsDoNotMatch()

    # Check if the username is already assigned.
    if User.query.filter_by(username=data['username']).first():
        raise exc.UsernameAlreadyTaken()

    # Check if the email address is already assigned.
    if User.query.filter_by(email=data['email']).first():
        raise exc.EmailAddressAlreadyTaken()

    # Try to create the user.
    try:
        user = User(
            firstname=str(data['firstname']),
            lastname=str(data['lastname']),
            username=str(data['username']),
            email=str(data['email']),
            password=bcrypt.generate_password_hash(str(data['password'])))
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return make_response('Created user.', 200)


# Verification routes #########################################################
@app.route('/verifications', methods=['GET'])
@adminRequired
def list_pending_validations(admin):
    '''Returns a list of all non verified users'''
    res = (db.session.query(User)
           .filter(~exists().where(UserVerification.user_id == User.id))
           .all())
    pending = []
    for user in res:
        pending.append({
            'id': user.id,
            'firstname': user.firstname,
            'lastname': user.lastname
        })
    return jsonify({'pending_validations': pending}), 200


@app.route('/verify/<int:id>', methods=['POST'])
@adminRequired
def verify_user(admin, id):
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.UserNotFound()
    if user.is_verified:
        raise exc.UserAlreadyVerified()

    user.verify(admin_id=admin.id)
    db.session.commit()
    return make_response('Verified user.', 201)


# User routes ################################################################
@app.route('/users', methods=['GET'])
@adminOptional
def list_users(admin):
    '''Return a list of all users'''
    result = User.query.filter(User.is_verified.is_(True)).all()
    if not admin:
        users = convert_minimal(result,
                                ['id', 'firstname', 'lastname', 'username'])
        return jsonify({'users': users}), 200

    users = [user.to_dict() for user in result]
    return jsonify({'users': users}), 200


@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    '''Return the user with the given id'''
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.UserNotFound()
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    fields = ['id', 'firstname', 'lastname', 'username', 'email', 'credit']
    user = convert_minimal(user, fields)
    return jsonify({'user': user}), 200


@app.route('/users/<int:id>', methods=['PUT'])
@adminRequired
def update_user(admin, id):
    '''Update the user with the given id'''
    data = json_body()
    # Delete all forbidden attributes from the list
    forbidden = ['id', 'credit', 'creation_date']
    for f in forbidden:
        if f in data:
            raise exc.ForbiddenField()

    # Query user
    user = result = User.query.filter(User.id == id).first()
    if not user:
        raise exc.UserNotFound()

    updated_fields = []

    # Update admin role
    if 'is_admin' in data and isinstance(data['is_admin'], bool):
        user.set_admin(is_admin=data['is_admin'], admin_id=admin.id)
        updated_fields.append('is_admin')
        del data['is_admin']

    # Check password
    if 'password' in data:
        if 'repeat' in data:
            if data['password'] == data['repeat']:
                password = str(data['password'])
                user.password = bcrypt.generate_password_hash(password)
                updated_fields.append('password')
                del data['repeat']
            else:
                raise exc.PasswordsDoNotMatch()
        else:
            raise exc.DataIsMissing()

        del data['password']

    # All other fields
    updateable = ['firstname', 'lastname', 'username', 'email']
    for item in data:
        if item in updateable:
            if not isinstance(data[item], str):
                raise exc.WrongType()
            setattr(user, item, str(data[item]))
            updated_fields.append(item)

    if len(updated_fields) == 0:
        raise exc.NothingHasChanged()

    # Apply changes
    db.session.commit()
    return jsonify({
        'message': 'Updated user.',
        'updated_fields': updated_fields
    }), 201


# Product routes #############################################################
@app.route('/products', methods=['GET'])
@adminOptional
def list_products(admin):
    '''Return a list of all products'''
    if not admin:
        result = Product.query.filter(Product.active.is_(True)).all()
    else:
        result = Product.query.all()
    products = convert_minimal(result, ['id', 'name', 'price', 'barcode',
                                        'active', 'countable', 'revokeable',
                                        'imagename'])
    return jsonify({'products': products}), 200


@app.route('/products', methods=['POST'])
@adminRequired
def create_product(admin):
    '''Create a product'''
    data = json_body()
    created_fields = []
    required = ['name', 'price']
    createable = {
        'name': str, 'price': int, 'barcode': str, 'active': bool,
        'countable': bool, 'revokeable': bool, 'imagename': str
    }

    # Check all required fields
    if any(x not in data for x in required):
        raise exc.DataIsMissing()

    # Check if a product with this name already exists
    if Product.query.filter_by(name=data['name']).first():
        raise exc.ProductAlreadyExists()

    # Check the given dataset
    for item in createable:
        if item in data:
            if not isinstance(data[item], createable[item]):
                raise exc.WrongType()
        else:
            raise exc.UnknownField(item)

    # Save the price and delete it from the data dictionary
    price = int(data['price'])
    del data['price']

    try:
        product = Product(**data)
        product.created_by = admin.id
        db.session.add(product)
        db.session.flush()
        product.set_price(price=price, admin_id=admin.id)
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created Product.'}), 201


@app.route('/products/<int:id>', methods=['GET'])
@adminOptional
def get_product(admin, id):
    '''Return the product with the given id'''
    result = (Product.query
              .filter(Product.id == id).first())
    if not result:
        raise exc.ProductNotFound()

    if not (result.active or admin):
        raise exc.UnauthorizedAccess()

    product = convert_minimal(result, ['id', 'name', 'price', 'barcode',
                                       'active', 'countable', 'revokeable',
                                       'imagename'])
    return jsonify({'product': product}), 200


@app.route('/products/<int:id>', methods=['PUT'])
@adminRequired
def update_product(admin, id):
    '''Update the product with the given id'''
    data = json_body()

    # Check, if the product exists.
    product = Product.query.filter_by(id=id).first()
    if not product:
        raise exc.ProductNotFound()

    # Check forbidden fields
    forbidden = ['creation_date', 'countable', 'revokeable']
    if any(x in data for x in forbidden):
        raise exc.ForbiddenField()

    updated_fields = []

    # Check types
    updateable = {
        'name': str, 'price': int, 'barcode': str, 'active': bool,
        'imagename': str
    }
    for item in data:
        if item in updateable:
            if not isinstance(data[item], updateable[item]):
                raise exc.WrongType(item)
        else:
            raise exc.UnknownField(item)

    # Check for price change
    if 'price' in data:
        price = int(data['price'])
        del data['price']
        if price != product.price:
            product.set_price(price=price, admin_id=admin.id)
            updated_fields.append('price')

    # Update all other fields
    for item in data:
        if not hasattr(product, item):
            raise exc.UnknownField()
        setattr(product, item, data[item])
        updated_fields.append(item)

    if len(updated_fields) == 0:
        raise exc.NothingHasChanged()

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Updated product.',
        'updated_fields': updated_fields
    }), 201


# Purchase routes ############################################################
@app.route('/purchases', methods=['GET'])
@adminOptional
def list_purchases(admin):
    '''Return a list of all purchases'''
    # Create a list for an admin
    if admin:
        res = Purchase.query.all()
        fields = ['id', 'timestamp', 'user_id', 'product_id', 'productprice',
                  'amount', 'revoked']
        return jsonify({'purchases': convert_minimal(res, fields)}), 200

    # Create a public list
    res = (db.session.query(Purchase)
           .filter(~exists().where(PurchaseRevoke.purchase_id == Purchase.id))
           .all())
    fields = ['id', 'timestamp', 'user_id', 'product_id']
    return jsonify({'purchases': convert_minimal(res, fields)}), 200


@app.route('/purchases', methods=['POST'])
def create_purchase():
    '''Create a purchase'''
    data = json_body()
    required = {'user_id': int, 'product_id': int, 'amount': int}
    for item in data:
        if item not in required:
            raise exc.UnknownField()
        if not isinstance(data[item], required[item]):
            raise exc.WrongType()

    # Check user
    user = User.query.filter_by(id=data['user_id']).first()
    if not user:
        raise exc.UserNotFound()
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    # Check product
    product = Product.query.filter_by(id=data['product_id']).first()
    if not product:
        raise exc.ProductNotFound()
    if not product.active:
        raise exc.ProductIsInactive()

    # Check amount
    if data['amount'] <= 0:
        raise exc.InvalidAmount()

    try:
        purchase = Purchase(**data)
        db.session.add(purchase)
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Purchase created.'}), 200


@app.route('/purchases/<int:id>', methods=['GET'])
def get_purchase(id):
    '''Return the purchase with the given id'''
    purchase = Purchase.query.filter_by(id=id).first()
    if not purchase:
        raise exc.PurchaseNotFound()
    fields = ['id', 'timestamp', 'user_id', 'product_id', 'amount', 'price',
              'productprice', 'revoked']
    return jsonify({'purchase': convert_minimal(purchase, fields)}), 200


@app.route('/purchases/<int:id>', methods=['PUT'])
def update_purchase(id):
    '''Update the purchase with the given id'''
    # Check purchase
    purchase = Purchase.query.filter_by(id=id).first()
    if not purchase:
        raise exc.PurchaseNotFound()

    data = json_body()
    updateable = {'revoked': bool, 'amount': int}
    for item in data:
        if item not in updateable:
            if hasattr(purchase, item):
                raise exc.ForbiddenField()
            raise exc.UnknownField()
        if not isinstance(data[item], updateable[item]):
            raise exc.WrongType()

    updated_fields = []

    # Handle purchase revoke
    if 'revoked' in data:
        if purchase.revoked == data['revoked']:
            raise exc.NothingHasChanged()
        purchase.toggle_revoke(revoked=data['revoked'])
        updated_fields.append('revoked')
        del data['revoked']

    # Handle all other fields
    for item in data:
        if not hasattr(purchase, item):
            raise exc.UnknownField()
        setattr(purchase, item, data[item])
        updated_fields.append(item)

    # Check the amount of updated fields
    if len(updated_fields) == 0:
        raise exc.NothingHasChanged()

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Updated purchase.',
        'updated_fields': updated_fields
    }), 201


# Deposit routes #############################################################
@app.route('/deposits', methods=['GET'])
def list_deposits():
    return make_response('Not implemented yet.', 400)


@app.route('/deposits', methods=['POST'])
@adminRequired
def create_deposit(admin):
    return make_response('Not implemented yet.', 400)


@app.route('/deposits/<int:id>', methods=['GET'])
def get_deposit(id):
    return make_response('Not implemented yet.', 400)


@app.route('/deposits/<int:id>', methods=['PUT'])
@adminRequired
def update_deposit(admin, id):
    return make_response('Not implemented yet.', 400)
