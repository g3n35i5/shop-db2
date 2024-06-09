#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from functools import wraps

import jwt
from flask import Response, request

import shop_db2.exceptions as exc
from shop_db2.api import app
from shop_db2.models import User


def checkIfUserIsValid(f):
    """This function checks whether the requested user exists, has been verified and is active.
    If this is not the case the request will be blocked.

    :param f:                  Is the wrapped function.

    :return:                   The wrapped function f with the additional parameter user.

    :raises EntryNotFound:     If the user with this ID does not exist.
    :raises UserIsNotVerified: If the user with this ID has not been verified yet.
    :raises UserIsInactive:    If the user with this ID is inactive.
    """

    @wraps(f)
    def decorator(*args, **kwargs):
        user = User.query.filter_by(id=kwargs["user_id"]).first()
        if not user:
            raise exc.EntryNotFound()

        # Check if the user has been verified.
        if not user.is_verified:
            raise exc.UserIsNotVerified()

        # Check if the user is inactive
        if not user.active:
            raise exc.UserIsInactive()

        # If all criteria are met, the requested function can be executed.
        return f(user, *args, **kwargs)

    return decorator


def adminRequired(f):
    """This function checks whether a valid token is contained in the request.
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
            token = request.headers["token"]
        except KeyError:
            raise exc.UnauthorizedAccess()

        # Is the token valid?
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"])
        except jwt.exceptions.DecodeError:
            raise exc.TokenIsInvalid()
        except jwt.ExpiredSignatureError:
            raise exc.TokenHasExpired()

        # If there is no admin object in the token and does the user does have
        # admin rights?
        try:
            admin_id = data["user"]["id"]
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
        return f(admin=admin, *args, **kwargs)

    return decorated


def adminOptional(f):
    """This function checks whether a valid token is contained in the request.
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
            token = request.headers["token"]
        except KeyError:
            return f(admin=None, *args, **kwargs)

        # Is the token valid?
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"])
        except (jwt.exceptions.DecodeError, jwt.ExpiredSignatureError):
            return f(admin=None, *args, **kwargs)

        # If there is no admin object in the token and does the user does have
        # admin rights?
        try:
            admin_id = data["user"]["id"]
            admin = User.query.filter(User.id == admin_id).first()
            assert admin.is_admin is True
        except KeyError:
            raise exc.TokenIsInvalid()
        except AssertionError:
            return f(admin=None, *args, **kwargs)

        # At this point it was verified that the request comes from an
        # admin and the request is executed. In addition, the user is
        # forwarded to the following function so that the administrator
        # responsible for any changes in the database can be traced.
        return f(admin=admin, *args, **kwargs)

    return decorated


def deprecate_route(message=""):
    """This decorator adds a warning message to the response header when the route is marked as deprecated.

    :param message: The message to be added to the response header.
    """

    def _decorator(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            data = func(*args, **kwargs)
            # Case 1: Tuple with (Response object, Status code)
            if isinstance(data, tuple):
                response: Response = data[0]
            # Case 2: Plain response object
            elif isinstance(data, Response):
                response: Response = data
            else:
                return data
            response.headers["Warning"] = message
            return data

        return _wrapper

    return _decorator
