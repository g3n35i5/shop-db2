#!/usr/bin/env python3

from sqlalchemy.exc import DontWrapMixin


class BaseException(Exception, DontWrapMixin):
    @classmethod
    def create_response(self):
        return jsonify(result=self.type, message=self.message), self.code


class NothingHasChanged(BaseException):
    def __init__(self):
        self.type = 'info'
        self.message = 'Nothing has changed.'
        self.code = 200


class UserAlreadyVerified(BaseException):
    def __init__(self):
        self.type = 'info'
        self.message = 'This user has already been verified.'
        self.code = 200


class DataIsMissing(BaseException):
    def __init__(self):
        self.type = 'error'
        self.message = 'Some or more details are missing.'
        self.code = 401


class WrongType(BaseException):
    def __init__(self):
        self.type = 'error'
        self.message = 'The data entered is of the wrong type.'
        self.code = 401


class UsernameAlreadyTaken(BaseException):
    def __init__(self):
        self.type = 'error'
        self.message = 'This username is already taken.'
        self.code = 401


class EmailAddressAlreadyTaken(BaseException):
    def __init__(self):
        self.type = 'error'
        self.message = 'This email address is already taken.'
        self.code = 401


class UserIsNotVerified(BaseException):
    def __init__(self):
        self.type = 'error'
        self.message = 'This user has not been verified yet.'
        self.code = 401


class ProductIsInactive(BaseException):
    def __init__(self):
        self.type = 'error'
        self.message = 'This product is inactive and cannot be purchased.'
        self.code = 401


class InvalidEmailAddress(BaseException):
    def __init__(self):
        self.type = 'error'
        self.message = 'The email address entered is not valid.'
        self.code = 401
