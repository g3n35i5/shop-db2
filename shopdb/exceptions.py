#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from sqlalchemy.exc import DontWrapMixin

"""
Base exception for all exceptions (needed for instance check)
"""


class ShopdbException(Exception, DontWrapMixin):
    type: str = None
    message: str = None
    code: int = None


"""
App related exceptions.

These exceptions handle all app errors.
"""


class MaintenanceMode(ShopdbException):
    type = 'error'
    message = 'The application is in maintenance mode. ' \
              'Please try again later. If you think this is an error, ' \
              'please contact the administrator.'
    code = 503


"""
Data related exceptions.

These exceptions handle all errors that occur when incorrect and/or incomplete
or unauthorized data is transferred.
"""


class DataIsMissing(ShopdbException):
    type = 'error'
    message = 'Some or more details are missing.'
    code = 401


class ForbiddenField(ShopdbException):
    type = 'error'
    message = 'One or more fields are forbidden.'
    code = 401


class WrongType(ShopdbException):
    type = 'error'
    message = 'The data entered is of the wrong type.'
    code = 401


class UnknownField(ShopdbException):
    type = 'error'
    message = 'Unknown field.'
    code = 401


class InvalidQueryParameters(ShopdbException):
    type = 'error'
    message = 'Invalid query parameters.'
    code = 400


class InvalidJSON(ShopdbException):
    type = 'error'
    message = 'The JSON data is corrupt.'
    code = 401


class InvalidData(ShopdbException):
    type = 'error'
    message = 'Invalid input data.'
    code = 401


class NoFileIncluded(ShopdbException):
    type = 'error'
    message = 'No file could be found in the request.'
    code = 401


class InvalidFilename(ShopdbException):
    type = 'error'
    message = 'The file is invalid.'
    code = 401


class BrokenImage(ShopdbException):
    type = 'error'
    message = 'The image file is broken.'
    code = 401


class ImageMustBeQuadratic(ShopdbException):
    type = 'error'
    message = 'The image must be quadratic.'
    code = 401


class InvalidFileType(ShopdbException):
    type = 'error'
    message = 'The file is of the wrong type.'
    code = 401


class FileTooLarge(ShopdbException):
    type = 'error'
    message = 'The file is too large.'
    code = 401


class InvalidAmount(ShopdbException):
    type = 'error'
    message = 'The quantity to be purchased is not permitted.'
    code = 401


"""
Entry related exceptions.

These exceptions handle all errors related to entries. This can be, for
example, that an entry already exists or cannot be updated or deleted. 
"""


class NothingHasChanged(ShopdbException):
    type = 'info'
    message = 'Nothing has changed.'
    code = 200


class CouldNotCreateEntry(ShopdbException):
    type = 'error'
    message = 'Could not create entry.'
    code = 401


class CouldNotUpdateEntry(ShopdbException):
    type = 'error'
    message = 'Could not update entry.'
    code = 401


class EntryNotFound(ShopdbException):
    type = 'error'
    message = 'There is no entry with this id.'
    code = 401


class EntryCanNotBeDeleted(ShopdbException):
    type = 'error'
    message = 'The entry can not be deleted.'
    code = 401


class EntryIsInactive(ShopdbException):
    type = 'error'
    message = 'This entry is inactive.'
    code = 401


class EntryIsNotForSale(ShopdbException):
    type = 'error'
    message = 'This entry is not for sale.'
    code = 400


class EntryAlreadyExists(ShopdbException):
    type = 'error'
    message = 'This entry already exists.'
    code = 401


class EntryNotRevocable(ShopdbException):
    type = 'error'
    message = 'This entry cannot be revoked.'
    code = 401


class NoRemainingTag(ShopdbException):
    type = 'error'
    message = 'There always has to be at least one tag per product.'
    code = 401


"""
User related exceptions.

These exceptions handle all errors related to users.
"""


class UserIsNotVerified(ShopdbException):
    type = 'error'
    message = 'This user has not been verified yet.'
    code = 401


class UserIsInactive(ShopdbException):
    type = 'error'
    message = 'This user account has been deactivated.'
    code = 401


class InsufficientCredit(ShopdbException):
    type = 'error'
    message = 'You do not have enough credit for this purchase'
    code = 401


class UserAlreadyVerified(ShopdbException):
    type = 'error'
    message = 'This user has already been verified.'
    code = 401


class UserNeedsPassword(ShopdbException):
    type = 'error'
    message = 'The user must first set a password before he can become ' \
              'an administrator.'
    code = 401


"""
Credential related exceptions.

These exceptions handle all errors related to permissions. This can be, for
example, that a user wants to perform an action for which he does not have the
authorization or that the session has expired, i.e. the token has become
invalid.
"""


class PasswordsDoNotMatch(ShopdbException):
    type = 'error'
    message = 'Password does not match the confirm password.'
    code = 401


class PasswordTooShort(ShopdbException):
    type = 'error'
    message = 'The password is too short.'
    code = 401


class InvalidCredentials(ShopdbException):
    type = 'error'
    message = 'A user with this access data was not found.'
    code = 401


class UnauthorizedAccess(ShopdbException):
    type = 'error'
    message = 'You do not have the authorization to perform this action.'
    code = 401


class TokenIsInvalid(ShopdbException):
    type = 'error'
    message = 'Your token is invalid.'
    code = 401


class TokenHasExpired(ShopdbException):
    type = 'error'
    message = 'Your Token has been expired.'
    code = 401


class NoRemainingAdmin(ShopdbException):
    type = 'error'
    message = 'There always has to be at least one admin. You cant remove' \
              'your admin privileges'
    code = 401
