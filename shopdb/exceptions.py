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
    type = 'error'
    message = 'This user has already been verified.'
    code = 401


class UserCanNotBeDeleted(BaseException):
    type = 'error'
    message = 'This user can not be deleted.'
    code = 401


class DataIsMissing(BaseException):
    type = 'error'
    message = 'Some or more details are missing.'
    code = 401


class ForbiddenField(BaseException):
    type = 'error'
    message = 'One or more fields are forbidden.'
    code = 401


class WrongType(BaseException):
    type = 'error'
    message = 'The data entered is of the wrong type.'
    code = 401


class UnknownField(BaseException):
    type = 'error'
    message = 'Unknown field.'
    code = 401


class CouldNotCreateEntry(BaseException):
    type = 'error'
    message = 'Could not create entry.'
    code = 401


class CouldNotUpdateEntry(BaseException):
    type = 'error'
    message = 'Could not update entry.'
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


class UserNotFound(BaseException):
    type = 'error'
    message = 'There is no user with this id.'
    code = 401


class InvalidAmount(BaseException):
    type = 'error'
    message = 'The quantity to be purchased is not permitted.'
    code = 401


class PurchaseNotFound(BaseException):
    type = 'error'
    message = 'There is no purchase with this id.'
    code = 401


class ProductNotFound(BaseException):
    type = 'error'
    message = 'There is no product with this id.'
    code = 401


class ProductIsInactive(BaseException):
    type = 'error'
    message = 'This product is inactive and cannot be purchased.'
    code = 401


class ProductAlreadyExists(BaseException):
    type = 'error'
    message = 'This product already exists.'
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


class InvalidJSON(BaseException):
    type = 'error'
    message = 'The JSON data is corrupt.'
    code = 401
