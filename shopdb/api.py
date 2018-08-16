#!/usr/bin/env python3

from shopdb.models import *
import shopdb.exceptions as exc
from flask import (Flask, request, g, make_response, jsonify)
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import sqlite3
import sqlalchemy
from sqlalchemy.exc import *
from functools import wraps
import datetime
import configuration as config
app = Flask(__name__)

# Default app settings (to suppress unittest warnings) will be overwritten.
app.config.from_object(config.BaseConfig)
db.init_app(app)
bcrypt = Bcrypt(app)


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
            return make_response('Token is missing.', 400)

        # Is the token valid?
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
        except jwt.exceptions.DecodeError:
            return make_response('Token is invalid.', 400)

        # TODO: Does the expiration date still have to be checked or is
        #       jwt.decode(...) already doing so?

        # If there is no admin object in the token and does the user does have
        # admin rights?
        try:
            admin_id = data['user']['id']
            admin = User.query.filter(User.id == admin_id)
            assert admin.is_admin is True
        except (KeyError, AssertionError):
            return make_response('Unauthorized access.', 400)

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
    if app.config['DEBUG']:
        raise error
    # Create, if possible, a user friendly response.
    try:
        return jsonify(result=error.type, message=error.message), error.code
    except AttributeError:
        raise error
    # If for some reason no exception has been raised yet, this is done now.
    raise error


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
            raise exc.UserNotFound()

    # Check, if the username is not available, if an email address is
    # available in the request.
    elif 'email' in data and data['email'] is not '':
        user = User.query.filter_by(email=str(data['email'])).first()
        if not user:
            raise exc.UserNotFound()

    # If no user with this data exists or there is no password in the
    # request, cancel the authentication.
    if not user or 'password' not in data:
        raise exc.DataIsMissing()

    # Check if the user has already been verified.
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    # Check if the password matches the user's password.
    if not bcrypt.check_password_hash(str(data['password']), user.password):
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
        raise UsernameAlreadyTaken()

    # Check if the email address is already assigned.
    if User.query.filter_by(email=data['email']).first():
        raise EmailAddressAlreadyTaken()

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
        raise CouldNotCreateEntry()

    return make_response('Created user.', 200)


# Verification routes #########################################################
@app.route('/verifications', methods=['GET'])
@adminRequired
def list_pending_validations(admin):
    '''Returns a list of all non verified users'''
    res = User.query.filter_by(is_verified is False).all()
    pending = []
    for user in res:
        pending.append({
            'id': user.id,
            'firstname': user.firstname,
            'lastname': user.lastname
        })
    return jsonify({'pending_validations': pending}), 200


@app.route('/verify', methods=['POST'])
@adminRequired
def verify_user(admin):
    # TODO: Verify the user with the given id
    return make_response('Not implemented yet.', 400)


# User routes ################################################################
@app.route('/users', methods=['GET'])
def list_users():
    '''Return a list of all users'''
    # TODO: Check which data may be returned. Admins can see everything,
    #       all others only a minimal version (e.g. name and id)
    return make_response('Not implemented yet.', 400)


@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    '''Return the user with the given id'''
    # TODO: Check which data may be returned. Admins can see everything,
    #       all others only a minimal version (e.g. name and id)
    #       We need the credit here, too (for the shop)
    return make_response('Not implemented yet.', 400)


@app.route('/users/<int:id>', methods=['PUT'])
@adminRequired
def update_user(admin):
    '''Update the user with the given id'''
    # TODO: If necessary, remove all attributes that either must not be
    #       set or do not differ from the version in the database.
    #       This reduces the risk of an error occurring.
    return make_response('Not implemented yet.', 400)


# Product routes #############################################################
@app.route('/products', methods=['GET'])
def list_products():
    '''Return a list of all products'''
    # TODO: Check which data may be returned. Admins can see everything,
    #       all others only a minimal version (e.g. name, id and price)
    return make_response('Not implemented yet.', 400)


@app.route('/products', methods=['POST'])
@adminRequired
def create_product(admin):
    '''Create a product'''
    return make_response('Not implemented yet.', 400)


@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    '''Return the product with the given id'''
    return make_response('Not implemented yet.', 400)


@app.route('/products/<int:id>', methods=['PUT'])
@adminRequired
def update_product(admin, id):
    '''Update the product with the given id'''
    return make_response('Not implemented yet.', 400)


# Purchase routes ############################################################
@app.route('/purchases', methods=['GET'])
def list_purchases():
    '''Return a list of all purchases'''
    return make_response('Not implemented yet.', 400)


@app.route('/purchases', methods=['POST'])
def create_purchase():
    '''Create a purchase'''
    return make_response('Not implemented yet.', 400)


@app.route('/purchases/<int:id>', methods=['GET'])
def get_purchase(id):
    '''Return the purchase with the given id'''
    return make_response('Not implemented yet.', 400)


@app.route('/purchases/<int:id>', methods=['PUT'])
@adminRequired
def update_purchase(admin, id):
    '''Update the purchase with the given id'''
    return make_response('Not implemented yet.', 400)


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
