#!/usr/bin/env python3

from sqlalchemy.exc import DontWrapMixin
from flask import jsonify
import pdb


class BaseException(Exception, DontWrapMixin):
    pass


class NothingHasChanged(BaseException):
    type = 'info'
    message = 'Nothing has changed.'
    code = 200


class UserAlreadyVerified(BaseException):
    type = 'info'
    message = 'This user has already been verified.'
    code = 200


class DataIsMissing(BaseException):
    type = 'error'
    message = 'Some or more details are missing.'
    code = 401


class WrongType(BaseException):
    type = 'error'
    message = 'The data entered is of the wrong type.'
    code = 401


class UsernameAlreadyTaken(BaseException):
    type = 'error'
    message = 'This username is already taken.'
    code = 401


class EmailAddressAlreadyTaken(BaseException):
    type = 'error'
    message = 'This email address is already taken.'
    code = 401


class UserIsNotVerified(BaseException):
    type = 'error'
    message = 'This user has not been verified yet.'
    code = 401


class ProductIsInactive(BaseException):
    type = 'error'
    message = 'This product is inactive and cannot be purchased.'
    code = 401


class InvalidEmailAddress(BaseException):
    type = 'error'
    message = 'The email address entered is not valid.'
    code = 401


class PasswordsDoNotMatch(BaseException):
    type = 'error'
    message = 'Password does not match the confirm password.'
    code = 401


class InvalidCredentials(BaseException):
    type = 'error'
    message = 'A user with this access data was not found.'
    code = 401


class UnauthorizedAccess(BaseException):
    type = 'error'
    message = 'You do not have the authorization to perform this action.'
    code = 401


class TokenIsInvalid(BaseException):
    type = 'error'
    message = 'Your token is invalid.'
    code = 401


class TokenHasExpired(BaseException):
    type = 'error'
    message = 'Your Token has been expired.'
    code = 401
