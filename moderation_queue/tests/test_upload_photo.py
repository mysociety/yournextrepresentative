# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from mock import Mock, patch

from os.path import join, realpath, dirname
from shutil import rmtree

from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils.six import text_type
from django.utils.six.moves.urllib_parse import urlsplit

from django_webtest import WebTest
from unittest import skip
from webtest import Upload

from ..models import QueuedImage
from mysite.helpers import mkdir_p

from candidates.models import LoggedAction
from candidates.management.images import (
    ImageDownloadException, download_image_from_url)

from candidates.tests.factories import PersonExtraFactory
from candidates.tests.uk_examples import UK2015ExamplesMixin

TEST_MEDIA_ROOT = realpath(join(dirname(__file__), 'media'))


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PhotoUploadImageTests(UK2015ExamplesMixin, WebTest):

    example_image_filename = join(
        settings.BASE_DIR, 'moderation_queue', 'tests', 'example-image.jpg'
    )

    @classmethod
    def setUpClass(cls):
        super(PhotoUploadImageTests, cls).setUpClass()
        storage = FileSystemStorage()
        desired_storage_path = join('queued-images', 'pilot.jpg')
        with open(cls.example_image_filename, 'rb') as f:
            cls.storage_filename = storage.save(desired_storage_path, f)
        mkdir_p(TEST_MEDIA_ROOT)

    @classmethod
    def tearDownClass(cls):
        rmtree(TEST_MEDIA_ROOT)
        super(PhotoUploadImageTests, cls).tearDownClass()

    def setUp(self):
        super(PhotoUploadImageTests, self).setUp()
        PersonExtraFactory.create(
            base__id='2009',
            base__name='Tessa Jowell'
        )
        self.test_upload_user = User.objects.create_user(
            'john',
            'john@example.com',
            'notagoodpassword',
        )
        self.test_upload_user.terms_agreement.assigned_to_dc = True
        self.test_upload_user.terms_agreement.save()

    def tearDown(self):
        super(PhotoUploadImageTests, self).tearDown()
        self.test_upload_user.delete()

    def test_photo_upload_through_image_field(self):
        queued_images = QueuedImage.objects.all()
        initial_count = queued_images.count()
        upload_form_url = reverse(
            'photo-upload',
            kwargs={'person_id': '2009'}
        )
        form_page_response = self.app.get(
            upload_form_url,
            user=self.test_upload_user
        )
        form = form_page_response.forms['person-upload-photo-image']
        with open(self.example_image_filename, 'rb') as f:
            form['image'] = Upload('pilot.jpg', f.read())
        form['why_allowed'] = 'copyright-assigned'
        form['justification_for_use'] = 'I took this photo'
        upload_response = form.submit()
        self.assertEqual(upload_response.status_code, 302)

        split_location = urlsplit(upload_response.location)
        self.assertEqual('/moderation/photo/upload/2009/success', split_location.path)

        queued_images = QueuedImage.objects.all()
        self.assertEqual(initial_count + 1, queued_images.count())

        queued_image = queued_images.last()
        self.assertEqual(queued_image.decision, 'undecided')
        self.assertEqual(queued_image.why_allowed, 'copyright-assigned')
        self.assertEqual(
            queued_image.justification_for_use,
            'I took this photo'
        )
        self.assertEqual(queued_image.person.id, 2009)
        self.assertEqual(queued_image.user, self.test_upload_user)

    def test_shows_photo_policy_text_in_photo_upload_page(self):
        upload_form_url = reverse(
            'photo-upload',
            kwargs={'person_id': '2009'}
        )
        response = self.app.get(
            upload_form_url,
            user=self.test_upload_user
        )
        self.assertContains(response, 'Photo policy')


@patch('moderation_queue.forms.requests')
@patch('candidates.management.images.requests')
@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PhotoUploadURLTests(UK2015ExamplesMixin, WebTest):

    example_image_filename = join(
        settings.BASE_DIR, 'moderation_queue', 'tests', 'example-image.jpg'
    )

    @classmethod
    def setUpClass(cls):
        super(PhotoUploadURLTests, cls).setUpClass()
        storage = FileSystemStorage()
        desired_storage_path = join('queued-images', 'pilot.jpg')
        with open(cls.example_image_filename, 'rb') as f:
            cls.storage_filename = storage.save(desired_storage_path, f)
        mkdir_p(TEST_MEDIA_ROOT)

    @classmethod
    def tearDownClass(cls):
        rmtree(TEST_MEDIA_ROOT)
        super(PhotoUploadURLTests, cls).tearDownClass()

    def setUp(self):
        super(PhotoUploadURLTests, self).setUp()
        PersonExtraFactory.create(
            base__id='2009',
            base__name='Tessa Jowell'
        )
        self.test_upload_user = User.objects.create_user(
            'john',
            'john@example.com',
            'notagoodpassword',
        )
        self.test_upload_user.terms_agreement.assigned_to_dc = True
        self.test_upload_user.terms_agreement.save()
        upload_form_url = reverse(
            'photo-upload',
            kwargs={'person_id': '2009'}
        )
        self.form_page_response = self.app.get(
            upload_form_url,
            user=self.test_upload_user
        )

    def get_and_head_methods(self, *all_mock_requests):
        return [
            getattr(mock_requests, attr)
            for mock_requests in all_mock_requests
            for attr in ('get', 'head')
        ]

    def successful_get_image(self, *all_mock_requests, **kwargs):
        content_type = kwargs.get('content_type', 'image/jpeg')
        headers = {'content-type': content_type}
        with open(self.example_image_filename, 'rb') as image:
            image_data = image.read()
            for mock_method in self.get_and_head_methods(
                    *all_mock_requests):
                setattr(
                    mock_method,
                    'return_value',
                    Mock(
                        status_code=200,
                        headers=headers,
                        # The chunk size is larger than the example
                        # image, so we don't need to worry about
                        # returning subsequent chunks.
                        iter_content=lambda **kwargs: [image_data],
                    ))

    def unsuccessful_get_image(self, *all_mock_requests):
        for mock_method in self.get_and_head_methods(
                *all_mock_requests):
            setattr(
                mock_method,
                'return_value',
                Mock(status_code=404))

    def valid_form(self):
        form = self.form_page_response.forms['person-upload-photo-url']
        form['image_url'] = 'http://foo.com/bar.jpg'
        form['why_allowed_url'] = 'copyright-assigned'
        form['justification_for_use_url'] = 'I took this photo'
        return form

    def invalid_form(self):
        return self.form_page_response.forms['person-upload-photo-url']

    def test_uploads_a_photo_from_a_url(self, *all_mock_requests):
        initial_count = QueuedImage.objects.all().count()
        self.successful_get_image(*all_mock_requests)
        self.valid_form().submit()
        final_count = QueuedImage.objects.all().count()
        self.assertEqual(final_count, initial_count + 1)

    def test_saves_the_form_values_correctly(self, *all_mock_requests):
        self.successful_get_image(*all_mock_requests)
        self.valid_form().submit()
        queued_image = QueuedImage.objects.all().last()
        self.assertEqual(queued_image.decision, 'undecided')
        self.assertEqual(queued_image.why_allowed, 'copyright-assigned')
        self.assertEqual(queued_image.justification_for_use, 'I took this photo')
        self.assertEqual(queued_image.person.id, 2009)
        self.assertEqual(queued_image.user, self.test_upload_user)

    def test_creates_a_logged_action(self, *all_mock_requests):
        initial_count = LoggedAction.objects.all().count()
        self.successful_get_image(*all_mock_requests)
        self.valid_form().submit()
        final_count = LoggedAction.objects.all().count()
        self.assertEqual(final_count, initial_count + 1)

    def test_loads_success_page_if_upload_was_successful(self, *all_mock_requests):
        self.successful_get_image(*all_mock_requests)
        upload_response = self.valid_form().submit()
        self.assertEqual(upload_response.status_code, 302)
        split_location = urlsplit(upload_response.location)
        self.assertEqual(split_location.path, '/moderation/photo/upload/2009/success')

    def test_fails_validation_if_image_does_not_exist(self, *all_mock_requests):
        self.unsuccessful_get_image(*all_mock_requests)
        upload_response = self.valid_form().submit()
        self.assertEqual(upload_response.status_code, 200)
        self.assertIn(
            'That URL produced an HTTP error status code: 404',
            upload_response.content.decode('utf-8'))

    def test_fails_validation_if_image_has_wrong_content_type(self, *all_mock_requests):
        self.successful_get_image(*all_mock_requests, content_type='text/html')
        upload_response = self.valid_form().submit()
        with open('/tmp/foo.html', 'wb') as f:
            f.write(upload_response.content)
        self.assertEqual(upload_response.status_code, 200)
        self.assertIn(
            "This URL isn&#39;t for an image - it had Content-Type: text/html",
            upload_response.content.decode('utf-8'))

    def test_loads_upload_photo_page_if_form_is_invalid(self, *all_mock_requests):
        self.successful_get_image(*all_mock_requests)
        upload_response = self.invalid_form().submit()
        self.assertContains(upload_response, '<h1>Upload a photo of Tessa Jowell</h1>')

    def test_upload_size_restriction_works(self, *all_mock_requests):
        self.successful_get_image(*all_mock_requests)
        with self.assertRaises(ImageDownloadException) as context:
            download_image_from_url('http://foo.com/bar.jpg', max_size_bytes=512)
        self.assertEqual(
            text_type(context.exception),
            'The image exceeded the maximum allowed size')
