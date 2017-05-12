# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from os.path import join, realpath, dirname
from shutil import rmtree

from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils.six.moves.urllib_parse import urlsplit

from django_webtest import WebTest
from webtest import Upload

from ..models import QueuedImage
from mysite.helpers import mkdir_p

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
