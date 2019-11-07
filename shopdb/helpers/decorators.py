#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from functools import wraps
from flask import request
import jwt
import shopdb.exceptions as exc
from shopdb.api import app
from shopdb.models import User


def checkIfUserIsValid(f):
    """
    This function checks whether the requested user exists, has been verified and is active.
    If this is not the case the request will be blocked.

    :param f:                  Is the wrapped function.

    :return:                   The wrapped function f with the additional parameter user.

    :raises EntryNotFound:     If the user with this ID does not exist.
    :raises UserIsNotVerified: If the user with this ID has not been verified yet.
    :raises UserIsInactive:    If the user with this ID is inactive.
    """

    @wraps(f)
    def decorator(*args, **kwargs):
        user = User.query.filter_by(id=kwargs['id']).first()
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
        except (jwt.exceptions.DecodeError, jwt.ExpiredSignatureError):
            return f(None, *args, **kwargs)

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
