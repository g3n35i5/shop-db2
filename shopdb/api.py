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
import glob
from sqlalchemy.sql import exists
from sqlalchemy.exc import *
from functools import wraps, reduce
import datetime
import configuration as config
import random
import os
import collections
from PIL import Image
import shutil

app = Flask(__name__)

# Default app settings (to suppress unittest warnings) will be overwritten.
app.config.from_object(config.BaseConfig)

# Setting strict slash mapping to false ('/foo/' and '/foo' are same this way)
app.url_map.strict_slashes = False

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
            element[field] = getattr(item, field, None)

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


def check_fields_and_types(data, required, optional=None):
    """
    This function checks the given data for its types and existence.
    Required fields must exist, optional fields must not.

    :param data:            The data sent to the API.
    :param required:        A dictionary with all required entries and their
                            types.
    :param optional:        A dictionary with all optional entries and their
                            types.

    :return:                None

    :raises DataIsMissing:  If a required field is not in the data.
    :raises WrongType:      If a field is of the wrong type.
    """

    if required and optional:
        allowed = dict(**required, **optional)
    elif required:
        allowed = required
    else:
        allowed = optional

    # Check if there is an unknown field in the data
    if not all(x in allowed for x in data):
        raise exc.UnknownField()

    # Check whether all required data is available
    if required and any(item not in data for item in required):
        raise exc.DataIsMissing()

    # Check all data (including optional data) for their types
    for key, value in data.items():
        if not isinstance(value, allowed.get(key)):
            raise exc.WrongType()


def check_allowed_parameters(allowed):
    """
    This method checks all GET parameters for their type.

    :param allowed:               A dictionary containing all allowed parameters
                                  and types.

    :return:                      A dictionary with all converted and checked
                                  parameters.

    :raises UnauthorizedAccess:   If there's an illegal parameter in the data.
    :raises WrongType:            If an argument is of the wrong type.
    """
    result = {}
    if any([argument not in allowed for argument in request.args]):
        raise exc.UnauthorizedAccess()

    for key in request.args:
        try:
            result[key] = allowed[key](request.args.get(key))
        except ValueError:
            raise exc.WrongType()

    return result


def update_fields(data, row, updated=None):
    """
    This helper function updates all fields defined in the dictionary "data"
    for a given database object "row". If modifications have already been made
    to the object, the names of the fields that have already been updated can
    be transferred with the "updated" list. All updated fields are added to
    this list.

    :param data:               The dictionary with all entries to be updated.
    :param row:                The database object to be updated.
    :param updated:            A list of all fields that have already been
                               updated.

    :return:                   A list with all already updated fields and
                               those that have been added.

    :raises NothingHasChanged: If no fields were changed during the update.
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

    :param data:                 Is the dictionary containing the data for the
                                 new user.

    :return:                     None

    :raises DataIsMissing:       If not all required data is available.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises PasswordsDoNotMatch: If the passwords do not match.
    :raises CouldNotCreateEntry: If the new user cannot be created.
    """

    required = {'lastname': str}
    optional = {'firstname': str, 'password': str, 'password_repeat': str}

    check_fields_and_types(data, required, optional)

    password = None

    if 'password' in data:
        if 'password_repeat' not in data:
            raise exc.DataIsMissing()

        password = data['password'].strip()
        repeat_password = data['password_repeat'].strip()

        # Check if the passwords match.
        if password != repeat_password:
            raise exc.PasswordsDoNotMatch()

        # Check the password length
        if len(password) < app.config['MINIMUM_PASSWORD_LENGTH']:
            raise exc.PasswordTooShort()

        password = bcrypt.generate_password_hash(data['password'])

    # Try to create the user.
    if 'firstname' in data:
        firstname = data['firstname']
    else:
        firstname = None
    try:
        user = User(
            firstname=firstname,
            lastname=data['lastname'],
            password=password)
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

    :param f:                Is the wrapped function.

    :return:                 Returns the wrapped function f with the
                             additional parameter admin, if present.
                             Otherwise, the parameter admin is None.

    :raises TokenIsInvalid:  If the token cannot be decoded.
    :raises TokenHasExpired: If the token has been expired.
    :raises TokenIsInvalid:  If no user object could be found in the decoded
                             token.
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


@app.before_request
def before_request_hook():
    """
    This function is executed before each request is processed. Its purpose is
    to check whether the application is currently in maintenance mode. If this
    is the case, the current request is aborted and a corresponding exception
    is raised. An exception to this is a request on the route
    "/maintenance" [POST]: Via this route the maintenance mode can be switched
    on and off (by an administrator) or on the route "/login", so that one can
    log in as administrator.

    :raises MaintenanceMode: if the application is in maintenance mode.
    """

    # Check for maintenance mode.
    exceptions = ['maintenance', 'login']

    if app.config.get('MAINTENANCE') and request.endpoint not in exceptions:
        raise exc.MaintenanceMode()


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
    if isinstance(error, exc.ShopdbException):
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
    """
    A route that simply returns that the backend is online.

    :return: A message which says that the backend is online.
    """
    return jsonify({'message': 'Backend is online.'})


@app.route('/maintenance', methods=['POST'], endpoint='maintenance')
@adminRequired
def set_maintenance(admin):
    """
    This route can be used by an administrator to switch the maintenance mode
    on or off.

    :param admin:              Is the administrator user, determined by
                               @adminRequired.

    :raises DataIsMissing:     If the maintenance state is not included
                               in the request.
    :raises UnknownField:      If an unknown parameter exists in the request
                               data.
    :raises InvalidType:       If one or more parameters have an invalid type.
    :raises NothingHasChanged: If the maintenance mode is not changed by the
                               request.

    :return:                   A message with the new maintenance mode.
    """

    data = json_body()
    # Check all items in the json body.
    required = {'state': bool}
    check_fields_and_types(data, required)

    # Get the current maintenance state.
    current_state = app.config['MAINTENANCE']

    # Get the new state.
    new_state = data['state']

    # Handle the request.
    if current_state == new_state:
        raise exc.NothingHasChanged()

    app.config['MAINTENANCE'] = new_state

    message = 'Turned maintenance mode ' + ('on.' if new_state else 'off.')
    return jsonify({'message': message})


@app.route('/images', methods=['GET'], defaults={'imagename': None})
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
            raise exc.EntryNotFound()


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
    if 'filename' not in file or file['filename'] == '':
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


# Backups route ###################################################
@app.route('/backups', methods=['GET'])
@adminRequired
def get_backups(admin):
    """
    Returns a dictionary with all backups in the backup folder.
    The following backup directory structure is assumed for this function:

    [Year]/[Month]/[Day]/shop-db_[Year]-[Month]-[Day]_[Hour]-[Minute].db

    For example:
    2019/02/07/shop-db_2019-02-07_15-00.db

    :return: A dictionary containing all backups and the timestamp of the
             latest backup.
    """
    data = {
        'backups': {},
        'latest': None
    }
    root_dir = app.config['BACKUP_DIR']
    start = root_dir.rfind(os.sep) + 1
    for path, dirs, files in os.walk(root_dir):
        # Ignore the root path
        if os.path.normpath(path) == os.path.normpath(root_dir):
            continue
        # Ignore all empty folders
        if not dirs and not files:
            continue

        folders = path[start:].split(os.sep)
        subdir = dict.fromkeys(files)

        parent = reduce(dict.get, folders[:-1], data['backups'])

        # We are in the day-directory of our tree
        if len(subdir) != 0:
            parent[folders[-1]] = [key for key in subdir.keys()]
        else:
            parent[folders[-1]] = subdir

    # Get the timestamp of the latest backup
    all_files = glob.glob(root_dir + '**/*.db', recursive=True)
    if all_files:
        latest = os.path.getctime(max(all_files, key=os.path.getctime))
        data['latest'] = datetime.datetime.fromtimestamp(latest)

    return jsonify(data)


# Financial overview route ###################################################
@app.route('/financial_overview', methods=['GET'])
@adminRequired
def get_financial_overview(admin):
    """
    The financial status of the entire project can be retrieved via this route.
    All purchases, deposits, payoffs, refunds and replenishmentcollections are
    used for this purpose. The items are cleared once to a number indicating
    whether the community has debt or surplus money. In addition, the
    individual items are returned separately in order to get a better
    breakdown of the items.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A dictionary with the individually calculated values.
    """

    # Query all purchases,
    purchases = Purchase.query.filter(Purchase.revoked.is_(False)).all()

    # Query all deposits.
    deposits = Deposit.query.filter(Deposit.revoked.is_(False)).all()

    # Query all payoffs.
    payoffs = Payoff.query.filter(Payoff.revoked.is_(False)).all()

    # Query all refunds.
    refunds = Refund.query.filter(Refund.revoked.is_(False)).all()

    # Query all replenishment collections.
    replcolls = (ReplenishmentCollection
                 .query
                 .filter(ReplenishmentCollection.revoked.is_(False))
                 .all())

    sum_pur = sum(list(map(lambda x: x.price, purchases)))
    sum_dep = sum(list(map(lambda x: x.amount, deposits)))
    sum_pay = sum(list(map(lambda x: x.amount, payoffs)))
    sum_ref = sum(list(map(lambda x: x.total_price, refunds)))
    sum_rep = sum(list(map(lambda x: x.price, replcolls)))

    # The financial income is limited only to the income from purchases.
    sum_incomes = sum([sum_pur])
    incomes = {
        'amount': sum_incomes,
        'items': [
            {'name': 'Purchases', 'amount': sum_pur}
        ]
    }

    # The financial expenses result from deposits, payoffs, refunds and
    # replenishmentcollections.
    sum_expenses = sum([sum_dep, sum_pay, sum_ref, sum_rep])
    expenses = {
        'amount': sum_expenses,
        'items': [
            {'name': 'Deposits', 'amount': sum_dep},
            {'name': 'Payoffs', 'amount': sum_pay},
            {'name': 'Refunds', 'amount': sum_ref},
            {'name': 'Replenishments', 'amount': sum_rep}
        ]
    }

    # The total balance is calculated as incomes minus expenses.
    total_balance = sum_incomes - sum_expenses

    financial_overview = {
        'total_balance': total_balance,
        'incomes': incomes,
        'expenses': expenses
    }
    return jsonify({'financial_overview': financial_overview}), 200


# Login route ################################################################
@app.route('/login', methods=['POST'], endpoint='login')
def login():
    """
    Registered users can log in on this route.

    :return:                    A temporary valid token, which users can use
                                to identify themselves when making requests to
                                the API.

    :raises DataIsMissing:      If the id or password (or both) is not included
                                in the request.
    :raises UnknownField:       If an unknown parameter exists in the request
                                data.
    :raises InvalidType:        If one or more parameters have an invalid type.
    :raises InvalidCredentials: If no user can be found with the given data.
    :raises UserIsNotVerified:  If the user has not yet been verified.
    """
    data = json_body()
    # Check all items in the json body.
    required = {'id': int, 'password': str}
    check_fields_and_types(data, required)

    # Try to get the user with the id
    user = User.query.filter_by(id=data['id']).first()

    # If no user with this data exists cancel the authentication.
    if not user:
        raise exc.InvalidCredentials()

    # Check if the user has already been verified.
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    # Check if the user has set a password.
    if not user.password:
        raise exc.InvalidCredentials()

    # Check if the password matches the user's password.
    if not bcrypt.check_password_hash(user.password, str(data['password'])):
        raise exc.InvalidCredentials()

    # Create a dictionary object of the user.
    fields = ['id', 'firstname', 'lastname', 'credit']
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

    :return:                     A message that the registration was successful.

    :raises CouldNotCreateEntry: If the new user cannot be created.
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
    fields = ['id', 'firstname', 'lastname']
    return jsonify({'pending_validations': convert_minimal(res, fields)}), 200


@app.route('/verify/<int:id>', methods=['POST'])
@adminRequired
def verify_user(admin, id):
    """
    Verify a user.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the user id.

    :return:                     A message that the verification was successful.

    :raises UserAlreadyVerified: If the user already has been verified.
    :raises DataIsMissing:       If the rank_id is not included in the request.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid
                                 type.
    :raises EntryNotFound:       If the rank to be assigned to the user does
                                 not exist.
    """
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.EntryNotFound()
    if user.is_verified:
        raise exc.UserAlreadyVerified()

    data = json_body()
    # Check all items in the json body.
    required = {'rank_id': int}
    check_fields_and_types(data, required)

    rank_id = data['rank_id']
    rank = Rank.query.filter_by(id=rank_id).first()
    if not rank:
        raise exc.EntryNotFound()

    user.verify(admin_id=admin.id, rank_id=rank_id)
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
        fields = ['id', 'firstname', 'lastname', 'rank_id']
        return jsonify({'users': convert_minimal(result, fields)}), 200

    fields = ['id', 'firstname', 'lastname', 'credit', 'is_admin',
              'creation_date', 'rank_id']
    return jsonify({'users': convert_minimal(result, fields)}), 200


@app.route('/users/<int:id>/favorites', methods=['GET'])
def get_user_favorites(id):
    """
    Returns a list with the IDs of a user's favorite products. The list is
    empty if no favourite products exist.

    :param id:                 Is the user id.

    :return:                   A list with the IDs of the favorite products.

    :raises EntryNotFound:     If the user with this ID does not exist.
    :raises UserIsNotVerified: If the user has not yet been verified.
    """
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.EntryNotFound()
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

    :raises EntryNotFound:     If the user with this ID does not exist.
    :raises UserIsNotVerified: If the user has not yet been verified.
    """
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.EntryNotFound()
    if not user.is_verified:
        raise exc.UserIsNotVerified()
    deposits = user.deposits.all()

    fields = ['id', 'timestamp', 'admin_id', 'amount', 'revoked', 'comment']
    new_deposits = convert_minimal(deposits, fields)

    return jsonify({'deposits': new_deposits}), 200


@app.route('/users/<int:id>/refunds', methods=['GET'])
def get_user_refunds(id):
    """
    Returns a list with all refunds of a user.

    :param id:                 Is the user id.

    :return:                   A list with all refunds of the user.

    :raises EntryNotFound:     If the user with this ID does not exist.
    :raises UserIsNotVerified: If the user has not yet been verified.
    """
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.EntryNotFound()
    if not user.is_verified:
        raise exc.UserIsNotVerified()
    result = user.refunds.all()

    fields = ['id', 'timestamp', 'admin_id', 'total_price', 'revoked',
              'comment']
    refunds = convert_minimal(result, fields)

    return jsonify({'refunds': refunds}), 200


@app.route('/users/<int:id>/purchases', methods=['GET'])
def get_user_purchases(id):
    """
    Returns a list with all purchases of a user.

    :param id:                 Is the user id.

    :return:                   A list with all purchases of the user.

    :raises EntryNotFound:     If the user with this ID does not exist.
    :raises UserIsNotVerified: If the user has not yet been verified.
    """
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.EntryNotFound()
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

    :raises EntryNotFound:     If the user with this ID does not exist.
    :raises UserIsNotVerified: If the user has not yet been verified.
    """
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.EntryNotFound()
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    fields = ['id', 'firstname', 'lastname', 'credit', 'rank_id',
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

    :raises EntryNotFound:        If the user with this ID does not exist.
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
        raise exc.EntryNotFound()

    # Raise an exception if the user has not been verified yet.
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    allowed = {
        'firstname': str,
        'lastname': str,
        'password': str,
        'password_repeat': str,
        'is_admin': bool,
        'rank_id': int}

    # Check the data for forbidden fields.
    check_forbidden(data, allowed, user)
    # Check all allowed fields and for their types.
    check_fields_and_types(data, None, allowed)

    updated_fields = []

    # Update admin role
    if 'is_admin' in data:
        user.set_admin(is_admin=data['is_admin'], admin_id=admin.id)
        if not user.is_admin:
            users = User.query.all()
            admins = list(filter(lambda x: x.is_admin, users))
            if not admins:
                raise exc.NoRemainingAdmin()

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
    updateable = ['firstname', 'lastname']
    check_forbidden(data, updateable, user)
    updated_fields = update_fields(data, user, updated=updated_fields)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Updated user.',
        'updated_fields': updated_fields
    }), 201


@app.route('/users/<int:id>', methods=['DELETE'])
@adminRequired
def delete_user(admin, id):
    """
    Delete a user. This is only possible if the user has not yet been verified.

    :param admin:                 Is the administrator user, determined by
                                  @adminRequired.
    :param id:                    Is the user id.

    :return:                      A message that the deletion was successful.

    :raises EntryNotFound:        If the user with this ID does not exist.
    :raises EntryCanNotBeDeleted: If the user has already been verified or the
                                  deletion cannot take place for any other
                                  reason.
    """
    # Check if the user exists
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.EntryNotFound()

    # Check if the user has been verified
    if user.is_verified:
        raise exc.EntryCanNotBeDeleted()

    # Delete the user
    try:
        db.session.delete(user)
        db.session.commit()
    except IntegrityError:
        raise exc.EntryCanNotBeDeleted()

    return jsonify({'message': 'User deleted.'}), 200


# Rank routes #############################################################
@app.route('/ranks', methods=['GET'])
def list_ranks():
    """
    Returns a list of all ranks.

    :return: A list of all ranks.
    """
    result = Rank.query.all()
    ranks = convert_minimal(result, ['id', 'name', 'debt_limit'])
    return jsonify({'ranks': ranks}), 200


# Tag routes #############################################################
@app.route('/tags', methods=['GET'])
def list_tags():
    """
    Returns a list of all tags.

    :return: A list of all tags.
    """
    result = Tag.query.all()
    tags = convert_minimal(result, ['id', 'name', 'created_by'])
    return jsonify({'tags': tags}), 200


@app.route('/tags/<int:id>', methods=['GET'])
def get_tag(id):
    """
    Returns the tag with the requested id.

    :param id:             Is the tag id.

    :return:               The requested tag as JSON object.

    :raises EntryNotFound: If the tag with this ID does not exist.
    """
    result = Tag.query.filter_by(id=id).first()
    if not result:
        raise exc.EntryNotFound()

    tag = convert_minimal(result, ['id', 'name', 'created_by'])[0]
    return jsonify({'tag': tag}), 200


@app.route('/tags/<int:id>', methods=['DELETE'])
@adminRequired
def delete_tag(admin, id):
    """
    Delete a tag.

    :param admin:                 Is the administrator user, determined by
                                  @adminRequired.
    :param id:                    Is the tag id.

    :return:                      A message that the deletion was successful.

    :raises EntryNotFound:        If the user with this ID does not exist.
    :raises EntryCanNotBeDeleted: If the tag can not be deleted.
    """
    tag = Tag.query.filter_by(id=id).first()
    if not tag:
        raise exc.EntryNotFound()

    # You can't delete the last remaining tag
    tags = Tag.query.all()
    if len(tags) == 1:
        raise exc.NoRemainingTag()

    # Check all product tags
    for product in tag.products:
        if len(product.tags) == 1:
            raise exc.NoRemainingTag()

    # Delete the tag.
    try:
        db.session.delete(tag)
        db.session.commit()
    except IntegrityError:
        raise exc.EntryCanNotBeDeleted()

    return jsonify({'message': 'Tag deleted.'}), 200


@app.route('/tags', methods=['POST'])
@adminRequired
def create_tag(admin):
    """
    Route to create a new tag.

    :param admin:                 Is the administrator user, determined by
                                  @adminRequired.

    :return:                      A message that the creation was successful.

    :raises DataIsMissing:        If one or more fields are missing to create
                                  the tag.
    :raises UnknownField:         If an unknown parameter exists in the request
                                  data.
    :raises InvalidType:          If one or more parameters have an invalid
                                  type.
    :raises EntryAlreadyExists:   If a tag with this name already exists.
    :raises CouldNotCreateEntry:  If the new tag cannot be added to the
                                  database.

    """
    data = json_body()
    required = {'name': str}

    # Check all required fields
    check_fields_and_types(data, required)

    # Check if a tag with this name already exists
    if Tag.query.filter_by(name=data['name']).first():
        raise exc.EntryAlreadyExists()

    try:
        tag = Tag(**data)
        tag.created_by = admin.id
        db.session.add(tag)
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created Tag.'}), 201


@app.route('/tags/<int:id>', methods=['PUT'])
@adminRequired
def update_tag(admin, id):
    """
    Update the tag with the given id.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the tag id.

    :return:                     A message that the update was
                                 successful and a list of all updated fields.

    :raises EntryNotFound:       If the tag with this ID does not exist.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid type.
    :raises CouldNotUpdateEntry: If any other error occurs.
    """
    data = json_body()

    # Check, if the product exists.
    tag = Tag.query.filter_by(id=id).first()
    if not tag:
        raise exc.EntryNotFound()

    updateable = {'name': str}

    # Check forbidden fields
    check_forbidden(data, updateable, tag)
    # Check types
    check_fields_and_types(data, None, updateable)

    updated_fields = update_fields(data, tag)
    tag.created_by = admin.id

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Updated tag.',
        'updated_fields': updated_fields
    }), 201


# Tag assignment routes ######################################################
@app.route('/tagassignment/<command>', methods=['POST'])
@adminRequired
def change_product_tag_assignment(admin, command):
    """
    Under this route, a tag can be added to a product or removed.

    :param admin:              Is the administrator user, determined by
                               @adminRequired.

    :return:                   A message that the assignment has been added or
                               removed.

    :raises ForbiddenField:    If a forbidden field is in the request data.
    :raises UnknownField:      If an unknown parameter exists in the request
                               data.
    :raises InvalidType:       If one or more parameters have an invalid type.
    :raises EntryNotFound      If the product with the specified ID does not
                               exist.
    :raises EntryNotFound:     If the tag with the specified ID does not exist.
    :raises NothingHasChanged: If no change occurred after the update or removal.
    """

    if command not in ['add', 'remove']:
        raise exc.UnauthorizedAccess()

    data = json_body()
    required = {'product_id': int, 'tag_id': int}

    # Check all required fields
    check_fields_and_types(data, required)

    # Check if the product exists.
    product = Product.query.filter_by(id=data['product_id']).first()
    if not product:
        raise exc.EntryNotFound()

    # Check if the tag exists.
    tag = Tag.query.filter_by(id=data['tag_id']).first()
    if not tag:
        raise exc.EntryNotFound()

    if command == 'add':
        if tag in product.tags:
            raise exc.NothingHasChanged()

        try:
            product.tags.append(tag)
            db.session.commit()
        except IntegrityError:
            raise exc.CouldNotUpdateEntry()

        return jsonify({'message': 'Tag assignment has been added.'}), 201
    else:
        if tag not in product.tags:
            raise exc.NothingHasChanged()

        if len(product.tags) <= 1:
            raise exc.NoRemainingTag()

        try:
            product.tags.remove(tag)
            db.session.commit()
        except IntegrityError:
            raise exc.CouldNotUpdateEntry()

        return jsonify({'message': 'Tag assignment has been removed.'}), 201


# Product routes #############################################################
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
              'revocable', 'imagename', 'tags']
    products = convert_minimal(result, fields)

    for product in products:
        product['tags'] = [t.id for t in product['tags']]
    return jsonify({'products': products}), 200


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
        raise exc.UnauthorizedAccess()

    fields = ['id', 'name', 'price', 'barcode', 'active', 'countable',
              'revocable', 'imagename', 'tags', 'creation_date']

    # Convert the product to a dictionary
    product = convert_minimal(product, fields)[0]

    # Convert the product tags
    product['tags'] = [t.id for t in product['tags']]

    return jsonify({'product': product}), 200


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

    return jsonify({'pricehistory': history}), 200


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

    allowed_params = {'limit': int}
    args = check_allowed_parameters(allowed_params)

    # All optional params
    limit = args.get('limit')

    res = Purchase.query
    # Create a list for an admin
    if admin:
        fields = ['id', 'timestamp', 'user_id', 'product_id', 'productprice',
                  'amount', 'revoked', 'price']
    else:
        # Only list non-revoked purchases
        res = res.filter(
            ~exists().where(PurchaseRevoke.purchase_id == Purchase.id))
        fields = ['id', 'timestamp', 'user_id', 'product_id']

    # Apply the limit if given
    if limit:
        res = res.order_by(Purchase.id.desc()).limit(limit)

    # Finish the query
    res = res.all()

    return jsonify({'purchases': convert_minimal(res, fields)}), 200


@app.route('/purchases', methods=['POST'])
def create_purchase():
    """
    Insert a new purchase.

    :return:                     A message that the creation was successful.

    :raises DataIsMissing:       If not all required data is available.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises EntryNotFound:       If the user with this ID does not exist.
    :raises UserIsNotVerified:   If the user has not yet been verified.
    :raises EntryNotFound:       If the product with this ID does not exist.
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
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    # Check product
    product = Product.query.filter_by(id=data['product_id']).first()
    if not product:
        raise exc.EntryNotFound()
    if not product.active:
        raise exc.EntryIsInactive()

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

    :param id:             Is the purchase id.

    :return:               The requested purchase as JSON object.

    :raises EntryNotFound: If the purchase with this ID does not exist.
    """
    purchase = Purchase.query.filter_by(id=id).first()
    if not purchase:
        raise exc.EntryNotFound()
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

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.

    :return:                     A message that the creation was successful.

    :raises DataIsMissing:       If not all required data is available.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises EntryNotFound:       If the user with this ID does not exist.
    :raises UserIsNotVerified:   If the user has not yet been verified.
    :raises InvalidAmount:       If amount is equal to zero.
    :raises CouldNotCreateEntry: If any other error occurs.
    """
    data = json_body()
    required = {'user_id': int, 'amount': int, 'comment': str}
    check_fields_and_types(data, required)

    # Check user
    user = User.query.filter_by(id=data['user_id']).first()
    if not user:
        raise exc.EntryNotFound()
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    # Check amount
    if data['amount'] == 0:
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

    :param id:             Is the deposit id.

    :return:               The requested deposit as JSON object.

    :raises EntryNotFound: If the deposit with this ID does not exist.
    """
    # Query the deposit
    res = Deposit.query.filter_by(id=id).first()
    # If it not exists, return an error
    if not res:
        raise exc.EntryNotFound()
    # Convert the deposit to a JSON friendly format
    fields = ['id', 'timestamp', 'user_id', 'amount', 'comment', 'revoked',
              'revokehistory']
    return jsonify({'deposit': convert_minimal(res, fields)[0]}), 200


@app.route('/deposits/<int:id>', methods=['PUT'])
@adminRequired
def update_deposit(admin, id):
    """
    Update the deposit with the given id.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the deposit id.

    :return:                     A message that the update was
                                 successful and a list of all updated fields.

    :raises EntryNotFound:       If the deposit with this ID does not exist.
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
        raise exc.EntryNotFound()

    data = json_body()

    if not data:
        raise exc.NothingHasChanged()

    updateable = {'revoked': bool}
    check_forbidden(data, updateable, deposit)
    check_fields_and_types(data, None, updateable)

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

    updateable = {'revoked': bool, 'comment': str}
    check_forbidden(data, updateable, replcoll)
    check_fields_and_types(data, None, updateable)

    updated_fields = []
    # Handle replenishmentcollection revoke
    if 'revoked' in data:
        if replcoll.revoked == data['revoked']:
            raise exc.NothingHasChanged()
        # Check if the revoke was caused through the replenishment_update and
        # therefor cant be changed
        if data['revoked'] == False:
            if not repls:
                raise exc.EntryNotRevocable()
        replcoll.toggle_revoke(revoked=data['revoked'], admin_id=admin.id)
        del data['revoked']
        updated_fields.append('revoked')

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
        if data['revoked'] == False:
            if not repls_nr:
                replcoll.toggle_revoke(revoked=False, admin_id=admin.id)
                message = message + (' Rerevoked ReplenishmentCollection ID: {}'
                                     .format(replcoll.id))
        repl.toggle_revoke(revoked=data['revoked'], admin_id=admin.id)
        del data['revoked']
        updated_fields.append('revoked')

    # Handle all other fields
    updated_fields = update_fields(data, repl, updated_fields)

    # Check if ReplenishmentCollection still has unrevoked Replenishments
    repls = replcoll.replenishments.filter_by(revoked=False).all()
    if ((not repls) and (replcoll.revoked == False)):
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


# Refund routes ##############################################################
@app.route('/refunds', methods=['GET'])
@adminRequired
def list_refunds(admin):
    """
    Returns a list of all refunds.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A list of all refunds.
    """
    refunds = Refund.query.all()
    fields = ['id', 'timestamp', 'user_id', 'total_price', 'comment',
              'revoked', 'admin_id']
    return jsonify({'refunds': convert_minimal(refunds, fields)}), 200


@app.route('/refunds/<int:id>', methods=['GET'])
def get_refund(id):
    """
    Returns the refund with the requested id.

    :param id:             Is the refund id.

    :return:               The requested refund as JSON object.

    :raises EntryNotFound: If the refund with this ID does not exist.
    """
    # Query the refund
    res = Refund.query.filter_by(id=id).first()
    # If it not exists, return an error
    if not res:
        raise exc.EntryNotFound()
    # Convert the refund to a JSON friendly format
    fields = ['id', 'timestamp', 'user_id', 'total_price', 'comment', 'revoked',
              'revokehistory']
    return jsonify({'refund': convert_minimal(res, fields)[0]}), 200


@app.route('/refunds', methods=['POST'])
@adminRequired
def create_refund(admin):
    """
    Insert a new refund.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.

    :return:                     A message that the creation was successful.

    :raises DataIsMissing:       If not all required data is available.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises EntryNotFound:       If the user with this ID does not exist.
    :raises UserIsNotVerified:   If the user has not yet been verified.
    :raises InvalidAmount:       If amount is equal to zero.
    :raises CouldNotCreateEntry: If any other error occurs.
    """
    data = json_body()
    required = {'user_id': int, 'total_price': int, 'comment': str}
    check_fields_and_types(data, required)

    # Check user
    user = User.query.filter_by(id=data['user_id']).first()
    if not user:
        raise exc.EntryNotFound()
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    # Check amount
    if data['total_price'] <= 0:
        raise exc.InvalidAmount()

    # Create and insert refund
    try:
        refund = Refund(**data)
        refund.admin_id = admin.id
        db.session.add(refund)
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created refund.'}), 200


@app.route('/refunds/<int:id>', methods=['PUT'])
@adminRequired
def update_refund(admin, id):
    """
    Update the refund with the given id.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the refund id.

    :return:                     A message that the update was
                                 successful and a list of all updated fields.

    :raises EntryNotFound:       If the refund with this ID does not exist.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid
                                 type.
    :raises NothingHasChanged:   If no change occurred after the update.
    :raises CouldNotUpdateEntry: If any other error occurs.
    """
    # Check refund
    refund = Refund.query.filter_by(id=id).first()
    if not refund:
        raise exc.EntryNotFound()

    data = json_body()

    if not data:
        raise exc.NothingHasChanged()

    updateable = {'revoked': bool}
    check_forbidden(data, updateable, refund)
    check_fields_and_types(data, None, updateable)

    # Handle refund revoke
    if 'revoked' in data:
        if refund.revoked == data['revoked']:
            raise exc.NothingHasChanged()
        refund.toggle_revoke(revoked=data['revoked'], admin_id=admin.id)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Updated refund.',
    }), 201


# Payoff routes ##############################################################
@app.route('/payoffs', methods=['GET'])
@adminRequired
def list_payoffs(admin):
    """
    Returns a list of all payoffs.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A list of all payoffs.
    """
    payoffs = Payoff.query.all()
    fields = ['id', 'timestamp', 'amount', 'comment', 'revoked', 'admin_id']
    return jsonify({'payoffs': convert_minimal(payoffs, fields)}), 200


@app.route('/payoffs/<int:id>', methods=['GET'])
@adminRequired
def get_payoff(admin, id):
    """
    Returns the payoff with the requested id.

    :param admin:          Is the administrator user, determined by
                           @adminRequired.
    :param id:             Is the payoff id.

    :return:               The requested payoff as JSON object.

    :raises EntryNotFound: If the payoff with this ID does not exist.
    """
    # Query the payoff
    res = Payoff.query.filter_by(id=id).first()
    # If it not exists, return an error
    if not res:
        raise exc.EntryNotFound()
    # Convert the payoff to a JSON friendly format
    fields = ['id', 'timestamp', 'amount', 'comment', 'revoked',
              'revokehistory']
    return jsonify({'payoff': convert_minimal(res, fields)[0]}), 200


@app.route('/payoffs', methods=['POST'])
@adminRequired
def create_payoff(admin):
    """
    Insert a new payoff.

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
    if data['amount'] <= 0:
        raise exc.InvalidAmount()

    # Create and insert payoff
    try:
        payoff = Payoff(**data)
        payoff.admin_id = admin.id
        db.session.add(payoff)
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created payoff.'}), 200


@app.route('/payoffs/<int:id>', methods=['PUT'])
@adminRequired
def update_payoff(admin, id):
    """
    Update the payoff with the given id.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the payoff id.

    :return:                     A message that the update was
                                 successful and a list of all updated fields.

    :raises EntryNotFound:       If the payoff with this ID does not exist.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid
                                 type.
    :raises NothingHasChanged:   If no change occurred after the update.
    :raises CouldNotUpdateEntry: If any other error occurs.
    """
    # Check payoff
    payoff = Payoff.query.filter_by(id=id).first()
    if not payoff:
        raise exc.EntryNotFound()

    data = json_body()

    if not data:
        raise exc.NothingHasChanged()

    updateable = {'revoked': bool}
    check_forbidden(data, updateable, payoff)
    check_fields_and_types(data, None, updateable)

    # Handle payoff revoke
    if 'revoked' in data:
        if payoff.revoked == data['revoked']:
            raise exc.NothingHasChanged()
        payoff.toggle_revoke(revoked=data['revoked'], admin_id=admin.id)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotUpdateEntry()

    return jsonify({
        'message': 'Updated payoff.',
    }), 201


# StocktakingCollection routes ##############################################
@app.route('/stocktakingcollections', methods=['GET'])
@adminRequired
def list_stocktakingcollections(admin):
    """
    Returns a list of all stocktakingcollections.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A list of all stocktakingcollections.
    """
    data = StocktakingCollection.query.all()
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
        if not Product.query.filter_by(id=product_id).first():
            raise exc.EntryNotFound()

    # Get all active product ids
    products = Product.query.filter(Product.active.is_(True)).all()
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
