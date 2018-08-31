from shopdb.api import *
import shopdb.models as models
import shopdb.exceptions as exc
from sqlalchemy.exc import *
from time import sleep
from base import u_emails, u_passwords, u_firstnames, u_lastnames, u_usernames
from base_api import BaseAPITestCase
from flask import json
import jwt
from copy import copy
import io
import os
import pdb


class UploadAPITestCase(BaseAPITestCase):
    def test_authorization(self):
        '''This route should only be available for admins.'''
        res = self.post(url='/upload', role=None,
                        content_type='multipart/form-data')
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url='/upload', role='user',
                        content_type='multipart/form-data')
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url='/upload', role='admin',
                        content_type='multipart/form-data')
        self.assertException(res, exc.NoFileIncluded)

    def test_upload_no_file_included(self):
        '''A request without any data should raise an error.'''
        res = self.post(url='/upload', role='admin',
                        content_type='multipart/form-data')
        self.assertException(res, exc.NoFileIncluded)

    def test_upload_invalid_extension(self):
        '''A request with an invalid file extension should raise an error.'''
        data = dict({'file': (io.BytesIO(b'abcdefg'), 'test.txt')})
        res = self.post(url='/upload', data=data, role='admin',
                        content_type='multipart/form-data')
        self.assertException(res, exc.InvalidFileType)

    def test_upload_file_too_large(self):
        '''A request with an file which is too large should raise an error.'''
        bytes = b'1' * 6 * 1024 * 1024
        data = dict({'file': (io.BytesIO(bytes), 'test.png')})
        res = self.post(url='/upload', data=data, role='admin',
                        content_type='multipart/form-data')
        self.assertException(res, exc.FileTooLarge)

    def test_upload_invalid_filename(self):
        '''A request with an invalid file extension should raise an error.'''
        data = dict({'file': (io.BytesIO(b'abcdefg'), '.txt')})
        res = self.post(url='/upload', data=data, role='admin',
                        content_type='multipart/form-data')
        self.assertException(res, exc.InvalidFilename)

    def test_upload_broken_image(self):
        '''A request with a broken imageshould raise an error.'''
        for ext in ['png', 'jpg', 'jpeg']:
            filepath = app.config['UPLOAD_FOLDER'] + 'broken_image.' + ext
            with open(filepath, 'rb') as test:
                imgStringIO = io.BytesIO(test.read())
            data = dict({'file': (imgStringIO, 'broken_image.' + ext)})
            res = self.post(url='/upload', data=data, role='admin',
                            content_type='multipart/form-data')
            self.assertException(res, exc.BrokenImage)

    def test_upload_valid_image(self):
        '''A request with valid images should work.'''
        for ext in ['png', 'jpg', 'jpeg']:
            filepath = app.config['UPLOAD_FOLDER'] + 'valid_image.' + ext
            with open(filepath, 'rb') as test:
                imgStringIO = io.BytesIO(test.read())
            data = dict({'file': (imgStringIO, 'valid_image.' + ext)})
            res = self.post(url='/upload', data=data, role='admin',
                            content_type='multipart/form-data')
            self.assertEqual(res.status_code, 200)
            data = json.loads(res.data)
            assert 'message' in data
            assert 'filename' in data
            self.assertEqual(data['message'], 'Image uploaded successfully.')
            assert data['filename'].endswith(ext)
            path = os.path.join(app.config['UPLOAD_FOLDER'], data['filename'])
            self.assertTrue(os.path.isfile(path))
            # Delete the created file from the upload folder
            os.remove(path)
