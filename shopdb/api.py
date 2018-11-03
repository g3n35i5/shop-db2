#!/usr/bin/env python3

from shopdb.models import *
import shopdb.exceptions as exc
from flask import (Flask, request, g, make_response, jsonify)
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.exceptions import RequestEntityTooLarge, NotFound
import jwt
import sqlite3
import sqlalchemy
from sqlalchemy.sql import exists
from sqlalchemy.exc import *
from functools import wraps
import datetime
import configuration as config
import random
import os
from PIL import Image
import shutil
app = Flask(__name__)

# Default app settings (to suppress unittest warnings) will be overwritten.
app.config.from_object(config.BaseConfig)
db.init_app(app)
bcrypt = Bcrypt(app)


def set_app(configuration):
    app.config.from_object(configuration)
    return app


def convert_minimal(data, fields):
    '''This function returns only the required attributes of all objects in
       given list.'''

    if not isinstance(data, list):
        data = [data]

    if len(data) == 0:
        return []
    out = []

    for item in data:
        element = {}
        for field in fields:
            element[field] = getattr(item, field)

        out.append(element)

    return out


def check_forbidden(data, forbidden_fields):
    '''This function checks whether a forbidden field is in a Dictionary
       and, if necessary, returns an error message and terminates the
       higher-level function. '''
    if any(x in data for x in forbidden_fields):
        raise exc.ForbiddenField()


def check_allowed_fields_and_types(data, allowed_fields):
    '''This function checks whether the data contains an invalid field.
       At the same time, all entries are checked for their type.'''
    if not all(x in allowed_fields for x in data):
        raise exc.UnknownField()

    for key, value in data.items():
        if not isinstance(value, allowed_fields[key]):
            raise exc.WrongType()


def insert_user(data):
    '''Helper function to create a user.'''
    required = ['firstname', 'lastname', 'username', 'email',
                'password', 'password_repeat']

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
    if data['password'] != data['password_repeat']:
        raise exc.PasswordsDoNotMatch()

    # Convert email address to lowercase.
    email = data['email'].lower()

    # Check if the username is already assigned.
    if User.query.filter_by(username=data['username']).first():
        raise exc.UsernameAlreadyTaken()

    # Check if the email address is already assigned.
    if User.query.filter_by(email=email).first():
        raise exc.EmailAddressAlreadyTaken()

    # Try to create the user.
    try:
        user = User(
            firstname=data['firstname'],
            lastname=data['lastname'],
            username=data['username'],
            email=email,
            password=bcrypt.generate_password_hash(data['password']))
        db.session.add(user)
    except IntegrityError:
        raise exc.CouldNotCreateEntry()


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
    # Catch the 404-error.
    if isinstance(error, NotFound):
        return jsonify(result='error', message='Page does not exist.'), 404
    # As long as the application is in debug mode, all other exceptions
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


@app.route('/configuration', methods=['GET'])
def get_config():
    config = {'DEBT_LIMIT':app.config['DEBT_LIMIT']}

    return jsonify({'configuration': config}), 200


@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Backend is online.'})


@app.route('/images/', methods=['GET'], defaults={'imagename': None})
@app.route('/images/<imagename>', methods=['GET'])
def get_image(imagename):
    if not imagename:
        return send_from_directory(app.config['UPLOAD_FOLDER'], 'default.png')
    else:
        if os.path.isfile(app.config['UPLOAD_FOLDER'] + imagename):
            return send_from_directory(app.config['UPLOAD_FOLDER'], imagename)
        else:
            raise exc.ImageNotFound()


@app.route('/upload', methods=['POST'])
@adminRequired
def upload(admin):
    # Get the file. Raise an error if its file exceedes the maximum file size
    # defined in the app configuration file.
    try:
        if 'file' not in request.files:
            raise exc.NoFileIncluded()
        file = request.files['file']
    except RequestEntityTooLarge:
        raise exc.FileTooLarge()
    # Check if the  file
    if not file:
        raise exc.NoFileIncluded()
    # Check if the filename is empty. There is no way to create a file with
    # empty filename in python so this can not be tested. Anyway, this is
    # a possible error vector.
    if file.filename == '':
        raise exc.InvalidFilename()

    # Check if the filename is valid
    filename = file.filename.split('.')[0]
    if filename is '' or not filename:
        raise exc.InvalidFilename()

    # Check the file extension
    extension = file.filename.split('.')[1].lower()
    valid_extension = extension in ['png', 'jpg', 'jpeg']
    if not valid_extension:
        raise exc.InvalidFileType()

    # Check if the image is a valid image file.
    try:
        # Save the image to a temporary file.
        temp_filename = '/tmp/' + file.filename
        file.save(temp_filename)
        image = Image.open(temp_filename)

    # An invalid file will lead to an exception.
    except IOError:
        os.remove(temp_filename)
        raise exc.BrokenImage()

    # Create a unique filename.
    can_be_used = False
    while not can_be_used:
        unique = ''.join(random.choice('0123456789abcdef') for i in range(32))
        filename = '.'.join([unique, extension])
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        can_be_used = not os.path.isfile(path)

    # Move the temporary image to its desination path.
    shutil.move(temp_filename, path)

    # Create an upload
    try:
        upload = Upload(filename=filename, admin_id=admin.id)
        db.session.add(upload)
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    # Make response
    return jsonify({
        'message': 'Image uploaded successfully.',
        'filename': filename}), 200


# Login route ################################################################
@app.route('/login', methods=['POST'])
def login():
    '''Authenticate a registered user'''
    data = json_body()
    user = None
    # Check all items in the json body.
    allowed = ['identifier', 'password']
    for item in data:
        if item not in allowed:
            raise exc.ForbiddenField()
        if not isinstance(data[item], str):
            raise exc.WrongType()

    if not all(x in data for x in allowed):
        raise exc.DataIsMissing()

    # Try to get the user with the identifier.
    if 'identifier' in data and data['identifier'] is not '':
        # Try the email address.
        user = User.query.filter_by(email=data['identifier']).first()
        # If there is no match, try the username.
        if not user:
            user = User.query.filter_by(username=data['identifier']).first()

    # If no user with this data exists or there is no password in the
    # request, cancel the authentication.
    if not user:
        raise exc.InvalidCredentials()
    if 'password' not in data:
        raise exc.DataIsMissing()

    # Check if the user has already been verified.
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    # Check if the password matches the user's password.
    if not bcrypt.check_password_hash(user.password, str(data['password'])):
        raise exc.InvalidCredentials()

    # Create a dictionary object of the user.
    fields = ['id', 'firstname', 'lastname', 'username', 'email', 'credit']
    d_user = convert_minimal(user, fields)[0]

    # Create a token.
    exp = datetime.datetime.now() + datetime.timedelta(minutes=15)
    token = jwt.encode({'user': d_user, 'exp': exp}, app.config['SECRET_KEY'])

    # Return the result.
    return jsonify({'result': True, 'token': token.decode('UTF-8')}), 200


# Register route #############################################################
@app.route('/register', methods=['POST'])
def register():
    '''Register a new user'''
    insert_user(json_body())
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created user.'}), 200


# Verification routes #########################################################
@app.route('/verifications', methods=['GET'])
@adminRequired
def list_pending_validations(admin):
    '''Returns a list of all non verified users'''
    res = (db.session.query(User)
           .filter(~exists().where(UserVerification.user_id == User.id))
           .all())
    fields = ['id', 'firstname', 'lastname', 'email']
    return jsonify({'pending_validations': convert_minimal(res, fields)}), 200


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
    return jsonify({'message': 'Verified user.'}), 201


# User routes ################################################################
@app.route('/users', methods=['GET'])
@adminOptional
def list_users(admin):
    '''Return a list of all users'''
    result = User.query.filter(User.is_verified.is_(True)).all()
    if not admin:
        fields = ['id', 'firstname', 'lastname', 'username']
        return jsonify({'users': convert_minimal(result, fields)}), 200

    fields = ['id', 'firstname', 'lastname', 'username', 'email', 'credit',
              'is_admin', 'creation_date']
    return jsonify({'users': convert_minimal(result, fields)}), 200

@app.route('/users/favorites/<int:id>', methods=['GET'])
def get_user_favorites(id):
    '''Return the user with the given id'''
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.UserNotFound()
    if not user.is_verified:
        raise exc.UserIsNotVerified()
    favorites = user.favorites

    return jsonify({'favorites': favorites}), 200


@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    '''Return the user with the given id'''
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.UserNotFound()
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    fields = ['id', 'firstname', 'lastname', 'username', 'email', 'credit',
              'is_admin']
    user = convert_minimal(user, fields)[0]
    return jsonify({'user': user}), 200


@app.route('/users/<int:id>', methods=['PUT'])
@adminRequired
def update_user(admin, id):
    '''Update the user with the given id'''
    data = json_body()

    # Check the data for forbidden fields.
    check_forbidden(data, ['id', 'credit', 'creation_date'])

    # Check all allowed fields and for their types.
    allowed = {
        'firstname': str,
        'lastname': str,
        'username': str,
        'email': str,
        'password': str,
        'password_repeat': str,
        'is_admin': bool}

    check_allowed_fields_and_types(data, allowed)

    # Query user
    user = User.query.filter(User.id == id).first()
    if not user:
        raise exc.UserNotFound()

    updated_fields = []

    # Update admin role
    if 'is_admin' in data:
        user.set_admin(is_admin=data['is_admin'], admin_id=admin.id)
        updated_fields.append('is_admin')
        del data['is_admin']

    # Check password
    if 'password' in data:
        if 'password_repeat' in data:
            if data['password'] == data['password_repeat']:
                password = str(data['password'])
                user.password = bcrypt.generate_password_hash(password)
                updated_fields.append('password')
                del data['password_repeat']
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


@app.route('/users/<int:id>', methods=['DELETE'])
@adminRequired
def delete_user(admin, id):
    '''Delete the user with the given id. This is only possible with
       non-verified users'''
    # Check if the user exists
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.UserNotFound()

    # Check if the user has been verified
    if user.is_verified:
        raise exc.UserCanNotBeDeleted()

    # Delete the user
    try:
        db.session.delete(user)
        db.session.commit()
    except IntegrityError:
        raise UserCanNotBeDeleted()

    return jsonify({'message': 'User deleted.'}), 200


# Product routes #############################################################
@app.route('/products', methods=['GET'])
@adminOptional
def list_products(admin):
    '''Return a list of all products'''
    if not admin:
        result = (Product.query
                  .filter(Product.active.is_(True))
                  .order_by(Product.name)
                  .all())
    else:
        result = Product.query.order_by(Product.name).all()
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
    for item in data:
        if item in createable:
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
    product = Product.query.filter(Product.id == id).first()
    if not product:
        raise exc.ProductNotFound()

    if not (product.active or admin):
        raise exc.UnauthorizedAccess()

    fields = ['id', 'name', 'price', 'barcode', 'active', 'countable',
              'revokeable', 'imagename']
    return jsonify({'product': convert_minimal(product, fields)[0]}), 200


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

    # Check for image change.
    if 'imagename' in data:
        imagename = data['imagename']
        del data['imagename']
        if imagename != product.imagename:
            upload = Upload.query.filter_by(filename=imagename).first()
            if not upload:
                raise exc.ImageNotFound()

            product.image_id = upload.id
            updated_fields.append('imagename')

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
                  'amount', 'revoked', 'price']
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

    # Check credit
    current_credit = user.credit
    future_credit = current_credit - (product.price*data['amount'])
    if future_credit <= app.config['DEPT_LIMIT']:
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
    '''Return the purchase with the given id'''
    purchase = Purchase.query.filter_by(id=id).first()
    if not purchase:
        raise exc.PurchaseNotFound()
    fields = ['id', 'timestamp', 'user_id', 'product_id', 'amount', 'price',
              'productprice', 'revoked', 'revokehistory']
    return jsonify({'purchase': convert_minimal(purchase, fields)[0]}), 200


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
@adminRequired
def list_deposits(admin):
    '''List all deposits'''
    deposits = Deposit.query.all()
    fields = ['id', 'timestamp', 'user_id', 'amount', 'comment', 'revoked',
              'admin_id']
    return jsonify({'deposits': convert_minimal(deposits, fields)}), 200


@app.route('/deposits', methods=['POST'])
@adminRequired
def create_deposit(admin):
    '''Create a deposit'''
    data = json_body()
    required = {'user_id': int, 'amount': int, 'comment': str}
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

    # Check amount
    if data['amount'] <= 0:
        raise exc.InvalidAmount()

    # Create and insert deposit
    try:
        deposit = Deposit(**data)
        deposit.admin_id = admin.id
        db.session.add(deposit)
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created deposit.'}), 200


@app.route('/deposits/<int:id>', methods=['GET'])
def get_deposit(id):
    # Query the deposit
    res = Deposit.query.filter_by(id=id).first()
    # If it not exists, return an error
    if not res:
        raise exc.DepositNotFound()
    # Convert the deposit to a JSON friendly format
    fields = ['id', 'timestamp', 'user_id', 'amount', 'comment', 'revoked',
              'revokehistory']
    return jsonify({'deposit': convert_minimal(res, fields)[0]}), 200


@app.route('/deposits/<int:id>', methods=['PUT'])
@adminRequired
def update_deposit(admin, id):
    '''Update the deposit with the given id'''
    # Check deposit
    deposit = Deposit.query.filter_by(id=id).first()
    if not deposit:
        raise exc.DepositNotFound()

    data = json_body()
    updateable = {'revoked': bool}
    for item in data:
        if item not in updateable:
            if hasattr(deposit, item):
                raise exc.ForbiddenField()
            raise exc.UnknownField()
        if not isinstance(data[item], updateable[item]):
            raise exc.WrongType()
    if any(x not in data for x in updateable):
        raise exc.NothingHasChanged()

    # Handle deposit revoke
    if 'revoked' in data:
        if deposit.revoked == data['revoked']:
            raise exc.NothingHasChanged()
        deposit.toggle_revoke(revoked=data['revoked'], admin_id=admin.id)

    # Check credit
    user = User.query.filter_by(id=deposit.user_id).first()
    current_credit = user.credit
    future_credit = current_credit - deposit.amount
    if future_credit <= app.config['DEPT_LIMIT']:
        raise exc.InsufficientCredit()

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Updated deposit.',
    }), 201


# ReplenishmentCollection routes ##############################################
@app.route('/replenishmentcollections', methods=['GET'])
@adminRequired
def list_replenishmentcollections(admin):
    '''List all replenishmentcollections.'''
    data = ReplenishmentCollection.query.all()
    fields = ['id', 'timestamp', 'admin_id', 'price', 'revoked']
    response = convert_minimal(data, fields)
    return jsonify({'replenishmentcollections': response}), 200


@app.route('/replenishmentcollections/<int:id>', methods=['GET'])
@adminRequired
def get_replenishmentcollection(admin, id):
    '''Get a single replenishmentcollection.'''
    replcoll = ReplenishmentCollection.query.filter_by(id=id).first()
    fields_replcoll = ['id', 'timestamp', 'admin_id', 'price', 'revoked',
                       'revokehistory']
    fields_repl = ['id', 'replcoll_id', 'product_id', 'amount', 'total_price']
    repls = replcoll.replenishments.all()

    response = []
    new_replcoll = {}
    for field in fields_replcoll:
        new_replcoll[field] = getattr(replcoll, field)
    new_replcoll['replenishments'] = convert_minimal(repls, fields_repl)
    response.append(new_replcoll)

    return jsonify({'replenishmentcollection': response}), 200


@app.route('/replenishmentcollections', methods=['POST'])
@adminRequired
def create_replenishmentcollection(admin):
    '''Create replenishmentcollection.'''
    data = json_body()
    required_data = {'admin_id': int, 'replenishments': list}
    required_repl = {'product_id': int, 'amount': int, 'total_price': int}

    # Check all required fields
    if any(x not in data for x in required_data):
        raise exc.DataIsMissing()

    for item in data:
        if item not in required_data:
            raise exc.UnknownField()
        if not isinstance(data[item], required_data[item]):
            raise exc.WrongType()

    repls = data['replenishments']

    for repl in repls:

        # Check all required fields
        if any(x not in repl for x in required_repl):
            raise exc.DataIsMissing()
        for item in repl:
            if item not in required_repl:
                raise exc.UnknownField()
            if not isinstance(repl[item], required_repl[item]):
                raise exc.WrongType()

        # Check amount
        if repl['amount'] <= 0:
            raise exc.InvalidAmount()
        # Check product
        product = Product.query.filter_by(id=repl['product_id']).first()
        if not product:
            raise exc.ProductNotFound()

    # Create and insert replenishmentcollection
    try:
        replcoll = ReplenishmentCollection(admin_id=data['admin_id'],
                                           revoked=False)
        db.session.add(replcoll)
        db.session.flush()

        for repl in repls:
            rep = Replenishment(replcoll_id = replcoll.id, **repl)
            db.session.add(rep)
        db.session.commit()

    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created deposit.'}), 201


@app.route('/replenishmentcollections/<int:id>', methods=['PUT'])
@adminRequired
def update_replenishmentcollection(admin, id):
    '''Update a replenishmentcollection.'''
    # Check ReplenishmentCollection
    replcoll = (ReplenishmentCollection.query.filter_by(id=id).first())
    if not replcoll:
        raise exc.ReplenishmentCollectionNotFound()

    data = json_body()
    updateable = {'revoked': bool}
    for item in data:
        if item not in updateable:
            if hasattr(replcoll, item):
                raise exc.ForbiddenField()
            raise exc.UnknownField()
        if not isinstance(data[item], updateable[item]):
            raise exc.WrongType()
    if data == {}:
        raise exc.DataIsMissing()

    # Handle deposit revoke
    if replcoll.revoked == data['revoked']:
        raise exc.NothingHasChanged()
    replcoll.toggle_revoke(revoked=data['revoked'], admin_id=admin.id)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Revoked ReplenishmentCollection.'}), 201


@app.route('/replenishments/<int:id>', methods=['PUT'])
@adminRequired
def update_replenishment(admin, id):
    '''Update a replenishment.'''
    # Check Replenishment
    repl = Replenishment.query.filter_by(id=id).first()
    if not repl:
        raise exc.ReplenishmentNotFound()

    # Data validation
    data = json_body()
    updateable = {'amount': int, 'total_price': int}
    for item in data:
        if item not in updateable:
            if hasattr(repl, item):
                raise exc.ForbiddenField()
            raise exc.UnknownField()
        if not isinstance(data[item], updateable[item]):
            raise exc.WrongType()

    # Check all required fields
    if any(x not in data for x in updateable):
        raise exc.DataIsMissing()

    updated_fields = []

    # Handle fields
    for item in data:
        if not getattr(repl, item) == data[item]:
            setattr(repl, item, data[item])
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
        'message': 'Updated replenishment.',
        'updated_fields': updated_fields
    }), 201

@app.route('/replenishments/<int:id>', methods=['DELETE'])
@adminRequired
def delete_replenishment(admin, id):
    '''Update a replenishment.'''
    # Check Replenishment
    repl = Replenishment.query.filter_by(id=id).first()
    if not repl:
        raise exc.ReplenishmentNotFound()
    # Get the corresponding ReplenishmentCollection
    replcoll = (ReplenishmentCollection.query.filter_by(id=repl.replcoll_id)
                .first())

    # Delete replenishment
    db.session.delete(repl)
    message = 'Deleted Replenishment.'

    # Check if ReplenishmentCollection still has Replenishments
    repls = replcoll.replenishments.all()
    if not repls:
        message = message + (' Deletetd ReplenishmentCollection ID: {}'
                             .format(replcoll.id))
        db.session.delete(replcoll)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({'message': message}), 201
