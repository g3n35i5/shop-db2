#!/usr/bin/env python3
import os.path

PATH = os.path.dirname(__file__)


class BaseConfig(object):
    SECRET_KEY = "YouWillNeverGuess"  # nosec
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    BACKUP_DIR = PATH + "/backups/"
    HOST = "127.0.0.1"
    PORT = 5000
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = PATH + "/shopdb/uploads/"
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024
    VALID_EXTENSIONS = ["png"]
    MINIMUM_PASSWORD_LENGTH = 6
    MAINTENANCE = False


class ProductiveConfig(BaseConfig):
    DEBUG = False
    TEST = False
    ENV = "productive"
    DATABASE_PATH = PATH + "/shopdb/shop.db"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + DATABASE_PATH


class DevelopmentConfig(BaseConfig):
    DEBUG = False
    TEST = True
    DEVELOPMENT = True
    ENV = "development"


class UnittestConfig(BaseConfig):
    PRESERVE_CONTEXT_ON_EXCEPTION = False
