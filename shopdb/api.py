#!/usr/bin/env python3

from shopdb.models import *
import shopdb.exceptions as exc
from flask import (Flask, request, g, make_response, jsonify,
                   send_from_directory)
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from werkzeug.exceptions import NotFound
import jwt
import base64
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
    """
    Sets all parameters of the applications to those defined in the dictionary
    "configuration" and returns the application object.

    :param configuration: The dictionary with all settings for the application

    :return:              The application object with the updated settings.
    """
    app.config.from_object(configuration)
    return app


def convert_minimal(data, fields):
    """
    This function returns only the required attributes of all objects in
    given list.

    :param data:   The object from which the attributes are obtained.
    :param fields: A list of all attributes to be output.

    :return:       A dictionary with all requested attributes.
    """

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


def check_forbidden(data, allowed_fields, row):
    """
    This function checks whether any illegal fields exist in the data sent to
    the API with the request. If so, an exception is raised and the request
    is canceled.

    :param data:             The data sent to the API.
    :param allowed_fields:   A list of all allowed fields.
    :param row:              The object for which you want to check whether the
                             fields are forbidden.

    :return:                 None

    :raises ForbiddenField : If a forbidden field is in the data.
    """
    for item in data:
        if (item not in allowed_fields) and (hasattr(row, item)):
            raise exc.ForbiddenField()


def check_required(data, required_fields):
    """
    This function checks whether all required fields are in a Dictionary
    and, if necessary, returns an error message.

    :param data:            The data sent to the API.
    :param required_fields: A list of all required fields.

    :return:                None

    :raises DataIsMissing:  If a required field is not in the data.
    """
    if any(item not in data for item in required_fields):
        raise exc.DataIsMissing()


def check_allowed_fields_and_types(data, allowed_fields):
    """
    This function checks whether the data contains an invalid field.
    At the same time, all entries are checked for their type.

    :param data:            The dictionary whose entries are to be checked.
    :param allowed_fields:  A dictionary with all allowed entries and their
                            types.

    :return:                None

    :raises UnknownField:   If there's an unknown field in the data.
    :raises WrongType:      If a field is of the wrong type.
    """

    if not all(x in allowed_fields for x in data):
        raise exc.UnknownField()

    for key, value in data.items():
        if not isinstance(value, allowed_fields[key]):
            raise exc.WrongType()


def update_fields(data, row, updated=None):
    """
    This helper function updates all fields defined in the dictionary "data"
    for a given database object "row". If modifications have already been made
    to the object, the names of the fields that have already been updated can
    be transferred with the "updated" list. All updated fields are added to
    this list.

    :param data:                The dictionary with all entries to be updated.
    :param row:                 The database object to be updated.
    :param updated:             A list of all fields that have already been
                                updated.

    :return:                    A list with all already updated fields and
                                those that have been added.

    :raises: NothingHasChanged: If no fields were changed during the update.
    """
    for item in data:
        if not getattr(row, item) == data[item]:
            setattr(row, item, data[item])
            if updated is not None:
                updated.append(item)
            else:
                updated = [item]

    if not updated or len(updated) == 0:
        raise exc.NothingHasChanged()

    return updated


def insert_user(data):
    """
    This help function creates a new user with the given data.

    :param data:                      Is the dictionary with all the data for
                                      the user.

    :return:                          None

    :raises DataIsMissing:            If not all required data is available.
    :raises WrongType:                If one or more data is of the wrong type.
    :raises PasswordsDoNotMatch:      If the passwords do not match.
    :raises UsernameAlreadyTaken:     If the username is already taken.
    :raises EmailAddressAlreadyTaken: If the email address is already taken.
    :raises CouldNotCreateEntry:      If the new user cannot be added to the
                                      database.
    """
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

    password = data['password'].strip()
    repeat_password = data['password_repeat'].strip()

    # Check if the passwords match.
    if password != repeat_password:
        raise exc.PasswordsDoNotMatch()

    # Check the password length
    if len(password) < app.config['MINIMUM_PASSWORD_LENGTH']:
        raise exc.PasswordTooShort()

    # Convert email address to lowercase.
    email = data['email'].strip().lower()

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
    """
    This function checks whether a valid token is contained in the request.
    If this is not the case, or the user has no admin rights, the request
    will be blocked.

    :param f:                   Is the wrapped function.

    :return:                    The wrapped function f with the additional
                                parameter admin.

    :raises UnauthorizedAccess: If no token object can be found in the request
                                header.
    :raises TokenIsInvalid:     If the token cannot be decoded.
    :raises TokenHasExpired:    If the token has been expired.
    :raises TokenIsInvalid:     If no user object could be found in the
                                decoded token.
    :raises UnauthorizedAccess: The user has no administrator privileges.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        # Does the request header contain a token?
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
    """
    This function checks whether a valid token is contained in the request.
    If this is not the case, or the user has no admin rights, the following
    function returns only a part of the available data.

    :param f:                   Is the wrapped function.

    :return:                    Returns the wrapped function f with the
                                additional parameter admin, if present.
                                Otherwise, the parameter admin is None.

    :raises TokenIsInvalid:     If the token cannot be decoded.
    :raises TokenHasExpired:    If the token has been expired.
    :raises TokenIsInvalid:     If no user object could be found in the
                                decoded token.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        # Does the request header contain a token?
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
    """
    This wrapper catches all exceptions and, if possible, returns a user
    friendly response. Otherwise, it will raise the error

    :param error: Is the exception to be raised.

    :return:      Return a json response with the message that the page cannot
                  be found if it is a 404 error.
    :return:      Return a json response with the custom exception message,
                  if it is a custom exception.

    :raises:      Raises the passed exception if the application is in debug
                  mode or cannot be interpreted.
    """
    # Perform a rollback. All changes that have not yet been committed are
    # thus reset.
    db.session.rollback()

    # Catch the 404-error.
    if isinstance(error, NotFound):
        return jsonify(result='error', message='Page does not exist.'), 404

    # As long as the application is in debug mode, all other exceptions
    # should be output immediately.
    if app.config['DEBUG'] and not app.config['DEVELOPMENT']:
        raise error  # pragma: no cover

    # Create, if possible, a user friendly response.
    if all(hasattr(error, item) for item in ['type', 'message', 'code']):
        return jsonify(result=error.type, message=error.message), error.code
    else:  # pragma: no cover
        raise error


def json_body():
    """
    Returns the json data from the current request.

    :return:             The json body from the current request.

    :raises InvalidJSON: If the json data cannot be interpreted.
    """
    jb = request.get_json()
    if jb is None:
        raise exc.InvalidJSON()
    return jb


@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Backend is online.'})


@app.route('/initial_setup', methods=['POST'])
def initial_setup():
    data = json_body()
    # Check whether there are already users in the database.
    # If this is the case, the request must be aborted immediately.
    if User.query.all():
        raise exc.UnauthorizedAccess()

    # Check whether all required objects exist in the data.
    required = ['user', 'init_token']
    try:
        assert (all(x in data for x in required))
    except AssertionError:
        raise exc.DataIsMissing()

    # Check the init token.
    if data['init_token'] != app.config['init_token']:
        raise exc.UnauthorizedAccess()

    # Handle the user.
    insert_user(data['user'])

    return jsonify({'message': 'shop.db was successfully initialized'}), 200


@app.route('/images/', methods=['GET'], defaults={'imagename': None})
@app.route('/images/<imagename>', methods=['GET'])
def get_image(imagename):
    """
    A picture can be requested via this route. If the image is not found or if
    the image name is empty, a default image will be returned.

    :param imagename: Is the name of the requested image.

    :return:          The requested image or the default image, if applicable.
    """
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
    """
    You can upload pictures via this route. The valid file formats can be
    set in the configuration under "VALID_EXTENSIONS".

    :param admin:                 Is the administrator user, determined by
                                  @adminRequired.

    :return:                      The generated file name under which the image
                                  has been stored.

    :raises NoFileIncluded:       If no data was found in the request.
    :raises InvalidFilename:      If the filename is empty empty or invalid in
                                  any other form.
    :raises InvalidFileType:      If the file format is not allowed.
    :raises FileTooLarge:         If the size of the file exceeds the maximum
                                  allowed file size.
    :raises BrokenImage:          If the image file could not be read.
    :raises ImageMustBeQuadratic: If the height and width of the image are not
                                  identical.
    :raises CouldNotCreateEntry:  If the new image cannot be added to the
                                  database.
    """
    # Get the file. Raise an exception if there is no data.
    file = request.get_json()
    if not file:
        raise exc.NoFileIncluded()

    # Check if the filename is empty. There is no way to create a file with
    # empty filename in python so this can not be tested. Anyway, this is
    # a possible error vector.
    if file['filename'] == '':
        raise exc.InvalidFilename()

    # Check if the filename is valid
    filename = file['filename'].split('.')[0]
    if filename is '' or not filename:
        raise exc.InvalidFilename()

    # Check the file extension
    extension = file['filename'].split('.')[1].lower()
    valid_extension = extension in app.config['VALID_EXTENSIONS']
    if not valid_extension:
        raise exc.InvalidFileType()

    # Check if the image data has a value field.
    if 'value' not in file:
        raise exc.NoFileIncluded()

    # Check the content size.
    if len(file['value']) > app.config.get('MAX_CONTENT_LENGTH'):
        raise exc.FileTooLarge()

    # Check if the image is a valid image file.
    try:
        # Save the image to a temporary file.
        temp_filename = '/tmp/' + file['filename']
        filedata = file['value']
        f = open(temp_filename, 'wb')
        f.write(base64.b64decode(filedata))
        f.close()
        image = Image.open(temp_filename)

    # An invalid file will lead to an exception.
    except IOError:
        os.remove(temp_filename)
        raise exc.BrokenImage()

    # Check the real extension again
    if image.format not in [x.upper() for x in app.config['VALID_EXTENSIONS']]:
        raise exc.InvalidFileType()

    # Check aspect ratio
    width, height = image.size
    if width != height:
        raise exc.ImageMustBeQuadratic()

    # Create a unique filename.
    can_be_used = False
    while not can_be_used:
        unique = ''.join(random.choice('0123456789abcdef') for i in range(32))
        filename = '.'.join([unique, extension])
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        can_be_used = not os.path.isfile(path)

    # Move the temporary image to its destination path.
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
    """
    Registered users can log in on this route.

    :return:                    A temporary valid token, which users can use
                                to identify themselves when making requests to
                                the API.

    :raises: DataIsMissing:     If the id or password (or both) is not included
                                in the request.
    :raises: UnknownField:      If an unknown parameter exists in the request
                                data.
    :raises InvalidType:        If one or more parameters have an invalid type.
    :raises InvalidCredentials: If no user can be found with the given data.
    :raises UserIsNotVerified:  If the user has not yet been verified.
    """
    data = json_body()
    # Check all items in the json body.
    allowed = {'id': int, 'password': str}
    check_required(data, allowed)
    check_allowed_fields_and_types(data, allowed)

    # Try to get the user with the id
    user = User.query.filter_by(id=data['id']).first()

    # If no user with this data exists cancel the authentication.
    if not user:
        raise exc.InvalidCredentials()

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
    """
    Registration of new users.

    :return:                          A message that the registration was
                                      successful.

    :raises DataIsMissing:            If not all required data is available.
    :raises WrongType:                If one or more data is of the wrong type.
    :raises PasswordsDoNotMatch:      If the passwords do not match.
    :raises UsernameAlreadyTaken:     If the username is already taken.
    :raises EmailAddressAlreadyTaken: If the email address is already taken.
    :raises CouldNotCreateEntry:      If the new user cannot be added to the
                                      database.
    """
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
    """
    Returns a list of all non verified users.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A list of all non verified users.
    """
    res = (db.session.query(User)
           .filter(~exists().where(UserVerification.user_id == User.id))
           .all())
    fields = ['id', 'firstname', 'lastname', 'email']
    return jsonify({'pending_validations': convert_minimal(res, fields)}), 200


@app.route('/verify/<int:id>', methods=['POST'])
@adminRequired
def verify_user(admin, id):
    """
    Verify a user.

    :param admin:                 Is the administrator user, determined by
                                  @adminRequired.
    :param id:                    Is the user id.

    :return:                      A message that the verification was
                                  successful.

    :raises: UserAlreadyVerified: If the user already has been verified.
    :raises: DataIsMissing:       If the rank_id is not included in the request.
    :raises: UnknownField:        If an unknown parameter exists in the request
                                  data.
    :raises InvalidType:          If one or more parameters have an invalid
                                  type.
    """
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.UserNotFound()
    if user.is_verified:
        raise exc.UserAlreadyVerified()

    data = json_body()
    # Check all items in the json body.
    allowed = {'rank_id': int}
    check_required(data, allowed)
    check_allowed_fields_and_types(data, allowed)

    user.verify(admin_id=admin.id, rank_id=data['rank_id'])
    db.session.commit()
    return jsonify({'message': 'Verified user.'}), 201


# User routes ################################################################
@app.route('/users', methods=['GET'])
@adminOptional
def list_users(admin):
    """
    Returns a list of all users. If this route is called by an
    administrator, all information is returned. However, if it is called
    without further rights, a minimal version is returned.

    :param admin: Is the administrator user, determined by @adminOptional.

    :return:      A list of all users.
    """
    result = User.query.filter(User.is_verified.is_(True)).all()
    if not admin:
        fields = ['id', 'firstname', 'lastname', 'username']
        return jsonify({'users': convert_minimal(result, fields)}), 200

    fields = ['id', 'firstname', 'lastname', 'username', 'email', 'credit',
              'is_admin', 'creation_date']
    return jsonify({'users': convert_minimal(result, fields)}), 200


@app.route('/users/<int:id>/favorites', methods=['GET'])
def get_user_favorites(id):
    """
    Returns a list with the IDs of a user's favorite products. The list is
    empty if no favourite products exist.

    :param id:                 Is the user id.

    :return:                   A list with the IDs of the favorite products.

    :raises UserNotFound:      If the user with this ID does not exist.
    :raises UserIsNotVerified: If the user has not yet been verified.
    """
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.UserNotFound()
    if not user.is_verified:
        raise exc.UserIsNotVerified()
    favorites = user.favorites

    return jsonify({'favorites': favorites}), 200


@app.route('/users/<int:id>/deposits', methods=['GET'])
def get_user_deposits(id):
    """
    Returns a list with all deposits of a user.

    :param id:                 Is the user id.

    :return:                   A list with all deposits of the user.

    :raises UserNotFound:      If the user with this ID does not exist.
    :raises UserIsNotVerified: If the user has not yet been verified.
    """
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.UserNotFound()
    if not user.is_verified:
        raise exc.UserIsNotVerified()
    deposits = user.deposits.all()

    fields = ['id', 'timestamp', 'admin_id', 'amount', 'revoked', 'comment']
    new_deposits = convert_minimal(deposits, fields)

    return jsonify({'deposits': new_deposits}), 200


@app.route('/users/<int:id>/purchases', methods=['GET'])
def get_user_purchases(id):
    """
    Returns a list with all purchases of a user.

    :param id:                 Is the user id.

    :return:                   A list with all purchases of the user.

    :raises UserNotFound:      If the user with this ID does not exist.
    :raises UserIsNotVerified: If the user has not yet been verified.
    """
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.UserNotFound()
    if not user.is_verified:
        raise exc.UserIsNotVerified()
    purchases = user.purchases.all()

    fields = ['id', 'timestamp', 'product_id', 'productprice', 'amount',
              'revoked', 'price']
    new_purchases = convert_minimal(purchases, fields)

    return jsonify({'purchases': new_purchases}), 200


@app.route('/users/<int:id>', methods=['GET'])
def get_user(id):
    """
    Returns the user with the requested id.

    :param id:                 Is the user id.

    :return:                   The requested user as JSON object.

    :raises UserNotFound:      If the user with this ID does not exist.
    :raises UserIsNotVerified: If the user has not yet been verified.
    """
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.UserNotFound()
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    fields = ['id', 'firstname', 'lastname', 'username', 'email', 'credit',
              'is_admin', 'creation_date', 'verification_date']
    user = convert_minimal(user, fields)[0]
    return jsonify({'user': user}), 200


@app.route('/users/<int:id>', methods=['PUT'])
@adminRequired
def update_user(admin, id):
    """
    Update the user with the given id.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the user id.
    :return:                     A message that the update was
                                 successful and a list of all updated fields.

    :raises UserNotFound:        If the user with this ID does not exist.
    :raises UserIsNotVerified:   If the user has not yet been verified.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid type.
    :raises PasswordsDoNotMatch: If the password and its repetition do not
                                 match.
    :raises DataIsMissing:       If the password is to be updated but no
                                 repetition of the password exists in the
                                 request.
    """
    data = json_body()

    # Query user
    user = User.query.filter(User.id == id).first()
    if not user:
        raise exc.UserNotFound()

    # Raise an exception if the user has not been verified yet.
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    allowed = {
        'firstname': str,
        'lastname': str,
        'username': str,
        'email': str,
        'password': str,
        'password_repeat': str,
        'is_admin': bool,
        'rank_id': int}

    # Check the data for forbidden fields.
    check_forbidden(data, allowed, user)
    # Check all allowed fields and for their types.
    check_allowed_fields_and_types(data, allowed)

    updated_fields = []

    # Update admin role
    if 'is_admin' in data:
        user.set_admin(is_admin=data['is_admin'], admin_id=admin.id)
        updated_fields.append('is_admin')
        del data['is_admin']

    # Update rank
    if 'rank_id' in data:
        user.set_rank_id(rank_id=data['rank_id'], admin_id=admin.id)
        updated_fields.append('rank_id')
        del data['rank_id']

    # Check password
    if 'password' in data:
        if 'password_repeat' in data:
            password = data['password'].strip()
            password_repeat = data['password_repeat'].strip()

            if password != password_repeat:
                raise exc.PasswordsDoNotMatch()

            if len(password) < app.config['MINIMUM_PASSWORD_LENGTH']:
                raise exc.PasswordTooShort()
            user.password = bcrypt.generate_password_hash(password)
            updated_fields.append('password')
            del data['password_repeat']
        else:
            raise exc.DataIsMissing()

        del data['password']

    # All other fields
    updateable = ['firstname', 'lastname', 'username', 'email']
    check_forbidden(data, updateable, user)
    updated_fields = update_fields(data, user, updated=updated_fields)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.UserCanNotBeUpdated()

    return jsonify({
        'message': 'Updated user.',
        'updated_fields': updated_fields
    }), 201


@app.route('/users/<int:id>', methods=['DELETE'])
@adminRequired
def delete_user(admin, id):
    """
    Delete a user. This is only possible if the user has not yet been verified.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the user id.

    :return:                     A message that the deletion was successful.

    :raises UserNotFound:        If the user with this ID does not exist.
    :raises UserCanNotBeDeleted: If the user has already been verified or the
                                 deletion cannot take place for any other
                                 reason.
    """
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
    """
    Returns a list of all products. If this route is called by an
    administrator, all information is returned. However, if it is called
    without further rights, a minimal version is returned.

    :param admin: Is the administrator user, determined by @adminOptional.

    :return:      A list of all products
    """
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
    """
    Route to create a new product.

    :param admin:                 Is the administrator user, determined by
                                  @adminRequired.

    :return:                      A message that the creation was successful.

    :raises DataIsMissing:        If one or more fields are missing to create
                                  the product.
    :raises UnknownField:         If an unknown parameter exists in the request
                                  data.
    :raises InvalidType:          If one or more parameters have an invalid
                                  type.
    :raises ProductAlreadyExists: If a product with this name already exists.
    :raises CouldNotCreateEntry:  If the new product cannot be added to the
                                  database.
    """
    data = json_body()
    required = ['name', 'price']
    createable = {
        'name': str, 'price': int, 'barcode': str, 'active': bool,
        'countable': bool, 'revokeable': bool, 'imagename': str
    }

    # Check all required fields
    check_required(data, required)

    # Check if a product with this name already exists
    if Product.query.filter_by(name=data['name']).first():
        raise exc.ProductAlreadyExists()

    # Check the given dataset
    check_allowed_fields_and_types(data, createable)

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
    """
    Returns the product with the requested id.

    :param admin:               Is the administrator user, determined by
                                @adminOptional.
    :param id:                  Is the product id.

    :return:                    The requested product as JSON object.

    :raises ProductNotFound:    If the product with this ID does not exist.
    :raises UnauthorizedAccess: If the product is inactive and the request
                                does not come from an administrator.
    """
    product = Product.query.filter(Product.id == id).first()
    if not product:
        raise exc.ProductNotFound()

    if not (product.active or admin):
        raise exc.UnauthorizedAccess()

    fields = ['id', 'name', 'price', 'barcode', 'active', 'countable',
              'revokeable', 'imagename', 'pricehistory']
    return jsonify({'product': convert_minimal(product, fields)[0]}), 200


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

    :raises ProductNotFound:     If the product with this ID does not exist.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid type.
    :raises ImageNotFound:       If the image is to be changed but no image
                                 with this name exists.
    :raises CouldNotUpdateEntry: If any other error occurs.
    """
    data = json_body()

    # Check, if the product exists.
    product = Product.query.filter_by(id=id).first()
    if not product:
        raise exc.ProductNotFound()

    updateable = {
        'name': str, 'price': int, 'barcode': str, 'active': bool,
        'imagename': str
    }

    # Check forbidden fields
    check_forbidden(data, updateable, product)
    # Check types
    check_allowed_fields_and_types(data, updateable)

    updated_fields = []

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


# Purchase routes ############################################################
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
    """
    Insert a new purchase.

    :return:                     A message that the creation was successful.

    :raises DataIsMissing:       If not all required data is available.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises UserNotFound:        If the user with this ID does not exist.
    :raises UserIsNotVerified:   If the user has not yet been verified.
    :raises ProductNotFound:     If the product with this ID does not exist.
    :raises ProductIsInactive:   If the product is inactive.
    :raises InvalidAmount:       If amount is less than or equal to zero.
    :raises InsufficientCredit:  If the credit balance of the user is not
                                 sufficient.
    :raises CouldNotCreateEntry: If any other error occurs.
    """
    data = json_body()
    required = {'user_id': int, 'product_id': int, 'amount': int}

    check_allowed_fields_and_types(data, required)
    check_required(data, required)

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

    :param id:                  Is the purchase id.

    :return:                    The requested purchase as JSON object.

    :raises PurchaseNotFound:   If the purchase with this ID does not exist.
    """
    purchase = Purchase.query.filter_by(id=id).first()
    if not purchase:
        raise exc.PurchaseNotFound()
    fields = ['id', 'timestamp', 'user_id', 'product_id', 'amount', 'price',
              'productprice', 'revoked', 'revokehistory']
    return jsonify({'purchase': convert_minimal(purchase, fields)[0]}), 200


@app.route('/purchases/<int:id>', methods=['PUT'])
def update_purchase(id):
    """
    Update the purchase with the given id.

    :param id:                   Is the purchase id.

    :return:                     A message that the update was
                                 successful and a list of all updated fields.

    :raises PurchaseNotFound:    If the purchase with this ID does not exist.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid type.
    :raises NothingHasChanged:   If no change occurred after the update.
    :raises CouldNotUpdateEntry: If any other error occurs.
    """
    # Check purchase
    purchase = Purchase.query.filter_by(id=id).first()
    if not purchase:
        raise exc.PurchaseNotFound()

    data = json_body()
    updateable = {'revoked': bool, 'amount': int}
    check_forbidden(data, updateable, purchase)
    check_allowed_fields_and_types(data, updateable)

    updated_fields = []

    # Handle purchase revoke
    if 'revoked' in data:
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


# Deposit routes #############################################################
@app.route('/deposits', methods=['GET'])
@adminRequired
def list_deposits(admin):
    """
    Returns a list of all deposits.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A list of all deposits.
    """
    deposits = Deposit.query.all()
    fields = ['id', 'timestamp', 'user_id', 'amount', 'comment', 'revoked',
              'admin_id']
    return jsonify({'deposits': convert_minimal(deposits, fields)}), 200


@app.route('/deposits', methods=['POST'])
@adminRequired
def create_deposit(admin):
    """
    Insert a new deposit.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:                     A message that the creation was successful.

    :raises DataIsMissing:       If not all required data is available.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises UserNotFound:        If the user with this ID does not exist.
    :raises UserIsNotVerified:   If the user has not yet been verified.
    :raises InvalidAmount:       If amount is less than or equal to zero.
    :raises CouldNotCreateEntry: If any other error occurs.
    """
    data = json_body()
    required = {'user_id': int, 'amount': int, 'comment': str}
    check_required(data, required)
    check_allowed_fields_and_types(data, required)

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
    """
    Returns the deposit with the requested id.

    :param id:                 Is the deposit id.

    :return:                   The requested deposit as JSON object.

    :raises DepositNotFound:   If the deposit with this ID does not exist.
    """
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
    """
    Update the deposit with the given id.

    :param id:                   Is the deposit id.

    :return:                     A message that the update was
                                 successful and a list of all updated fields.

    :raises DepositNotFound:     If the deposit with this ID does not exist.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid type.
    :raises NothingHasChanged:   If no change occurred after the update.
    :raises CouldNotUpdateEntry: If any other error occurs.
    """
    # Check deposit
    deposit = Deposit.query.filter_by(id=id).first()
    if not deposit:
        raise exc.DepositNotFound()

    data = json_body()

    if not data:
        raise exc.NothingHasChanged()

    updateable = {'revoked': bool}
    check_forbidden(data, updateable, deposit)
    check_allowed_fields_and_types(data, updateable)

    # Handle deposit revoke
    if 'revoked' in data:
        if deposit.revoked == data['revoked']:
            raise exc.NothingHasChanged()
        deposit.toggle_revoke(revoked=data['revoked'], admin_id=admin.id)

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
    """List all replenishmentcollections."""
    data = ReplenishmentCollection.query.all()
    fields = ['id', 'timestamp', 'admin_id', 'price', 'revoked']
    response = convert_minimal(data, fields)
    return jsonify({'replenishmentcollections': response}), 200


@app.route('/replenishmentcollections/<int:id>', methods=['GET'])
@adminRequired
def get_replenishmentcollection(admin, id):
    """Get a single replenishmentcollection."""
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
    """Create replenishmentcollection."""
    data = json_body()
    required_data = {'admin_id': int, 'replenishments': list}
    required_repl = {'product_id': int, 'amount': int, 'total_price': int}

    # Check all required fields
    check_required(data, required_data)
    check_allowed_fields_and_types(data, required_data)

    repls = data['replenishments']

    for repl in repls:

        # Check all required fields
        check_required(repl, required_repl)
        check_allowed_fields_and_types(repl, required_repl)

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
            rep = Replenishment(replcoll_id=replcoll.id, **repl)
            db.session.add(rep)
        db.session.commit()

    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created deposit.'}), 201


@app.route('/replenishmentcollections/<int:id>', methods=['PUT'])
@adminRequired
def update_replenishmentcollection(admin, id):
    """Update a replenishmentcollection."""
    # Check ReplenishmentCollection
    replcoll = (ReplenishmentCollection.query.filter_by(id=id).first())
    if not replcoll:
        raise exc.ReplenishmentCollectionNotFound()

    data = json_body()

    if data == {}:
        raise exc.NothingHasChanged()

    updateable = {'revoked': bool}
    check_forbidden(data, updateable, replcoll)
    check_allowed_fields_and_types(data, updateable)

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
    """Update a replenishment."""
    # Check Replenishment
    repl = Replenishment.query.filter_by(id=id).first()
    if not repl:
        raise exc.ReplenishmentNotFound()

    # Data validation
    data = json_body()
    updateable = {'amount': int, 'total_price': int}
    check_forbidden(data, updateable, repl)
    check_allowed_fields_and_types(data, updateable)
    check_required(data, updateable)

    updated_fields = update_fields(data, repl)

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
    """Update a replenishment."""
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
        message = message + (' Deleted ReplenishmentCollection ID: {}'
                             .format(replcoll.id))
        db.session.delete(replcoll)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({'message': message}), 201
