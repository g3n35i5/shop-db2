from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json
import base64
import os


class UploadAPITestCase(BaseAPITestCase):
    def test_authorization(self):
        """This route should only be available for admins."""
        res = self.post(url='/upload', role=None)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url='/upload', role='user')
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url='/upload', role='admin')
        self.assertException(res, exc.NoFileIncluded)
        self.assertEqual(len(Upload.query.all()), 0)

    def test_upload_no_file_included(self):
        """A request without any data should raise an error."""
        res = self.post(url='/upload', role='admin')
        self.assertException(res, exc.NoFileIncluded)
        self.assertEqual(len(Upload.query.all()), 0)

    def test_upload_empty_filename(self):
        """A request with an empty filename should raise an error."""
        image = {'value': base64.b64encode(b'abc').decode()}
        res = self.post(url='/upload', data=image, role='admin')
        self.assertException(res, exc.InvalidFilename)
        self.assertEqual(len(Upload.query.all()), 0)

    def test_upload_no_value_field(self):
        """A request without a value should raise an error."""
        image = {'filename': 'test.png'}
        res = self.post(url='/upload', data=image, role='admin')
        self.assertException(res, exc.NoFileIncluded)
        self.assertEqual(len(Upload.query.all()), 0)

    def test_upload_invalid_extension(self):
        """A request with an invalid file extension should raise an error."""
        image = {'filename': 'test.abc',
                 'value': base64.b64encode(b'abc').decode()}
        res = self.post(url='/upload', data=image, role='admin')
        self.assertException(res, exc.InvalidFileType)
        self.assertEqual(len(Upload.query.all()), 0)

    def test_upload_file_too_large(self):
        """A request with an file which is too large should raise an error."""
        bytes = b'1' * 6 * 1024 * 1024
        image = {'filename': 'test.png',
                 'value': base64.b64encode(bytes).decode()}
        res = self.post(url='/upload', data=image, role='admin')
        self.assertException(res, exc.FileTooLarge)
        self.assertEqual(len(Upload.query.all()), 0)

    def test_upload_invalid_filename(self):
        """A request with an invalid file extension should raise an error."""
        image = {'filename': '.abc', 'value': base64.b64encode(b'abc').decode()}
        res = self.post(url='/upload', data=image, role='admin')
        self.assertException(res, exc.InvalidFilename)
        self.assertEqual(len(Upload.query.all()), 0)

    def test_upload_broken_image(self):
        """A request with a broken image should raise an error."""
        filepath = app.config['UPLOAD_FOLDER'] + 'broken_image.png'
        with open(filepath, 'rb') as test:
            bytes = test.read()
        image = {'filename': 'broken.png',
                 'value': base64.b64encode(bytes).decode()}
        res = self.post(url='/upload', data=image, role='admin')
        self.assertException(res, exc.BrokenImage)
        self.assertEqual(len(Upload.query.all()), 0)

    def test_invalid_filetype_hidden_behind_valid_filename(self):
        """A request an invalid file type should raise an error."""
        filepath = app.config['UPLOAD_FOLDER'] + 'valid_image.jpg'
        with open(filepath, 'rb') as test:
            bytes = test.read()
        image = {'filename': 'hidden_invalid_filetype.png',
                 'value': base64.b64encode(bytes).decode()}
        res = self.post(url='/upload', data=image, role='admin')
        self.assertException(res, exc.InvalidFileType)
        self.assertEqual(len(Upload.query.all()), 0)

    def test_upload_non_quadratic_image(self):
        filepath = app.config['UPLOAD_FOLDER'] + 'non_quadratic.png'
        with open(filepath, 'rb') as test:
            bytes = test.read()
        image = {'filename': 'non_quadratic.png',
                 'value': base64.b64encode(bytes).decode()}
        res = self.post(url='/upload', data=image, role='admin')
        self.assertException(res, exc.ImageMustBeQuadratic)
        self.assertEqual(len(Upload.query.all()), 0)

    def test_upload_valid_image(self):
        """A request with valid images should work."""
        filepath = app.config['UPLOAD_FOLDER'] + 'valid_image.png'
        with open(filepath, 'rb') as test:
            bytes = test.read()
        image = {'filename': 'valid.png',
                 'value': base64.b64encode(bytes).decode()}
        res = self.post(url='/upload', data=image, role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'message' in data
        assert 'filename' in data
        self.assertEqual(data['message'], 'Image uploaded successfully.')
        assert data['filename'].endswith('png')
        path = os.path.join(app.config['UPLOAD_FOLDER'], data['filename'])
        self.assertTrue(os.path.isfile(path))
        upload = Upload.query.filter_by(filename=data['filename']).first()
        self.assertTrue(upload)
        self.assertEqual(upload.filename, data['filename'])
        self.assertEqual(upload.admin_id, 1)
        # Delete the created file from the upload folder
        os.remove(path)
