# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
from os.path import join, realpath, dirname
import re
from shutil import rmtree

from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils.six.moves.urllib_parse import urlsplit

from usersettings.shortcuts import get_current_usersettings

from PIL import Image
from io import BytesIO
from django_webtest import WebTest
from webtest import Upload
from mock import patch

from popolo.models import Person
from ..models import QueuedImage, PHOTO_REVIEWERS_GROUP_NAME
from candidates.models import LoggedAction, ImageExtra
from mysite.helpers import mkdir_p

from candidates.tests.factories import (
    AreaTypeFactory, ElectionFactory, PostExtraFactory,
    ParliamentaryChamberFactory, PersonExtraFactory,
    CandidacyExtraFactory, PartyExtraFactory,
    PartyFactory, PartySetFactory, AreaFactory
)
from candidates.tests.settings import SettingsMixin
from candidates.tests.uk_examples import UK2015ExamplesMixin

TEST_MEDIA_ROOT = realpath(join(dirname(__file__), 'media'))


def get_image_type_and_dimensions(image_data):
    image = Image.open(BytesIO(image_data))
    return {
        'format': image.format,
        'width': image.size[0],
        'height': image.size[1],
    }


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class PhotoReviewTests(SettingsMixin, UK2015ExamplesMixin, WebTest):

    example_image_filename = join(
        settings.BASE_DIR, 'moderation_queue', 'tests', 'example-image.jpg'
    )

    @classmethod
    def setUpClass(cls):
        super(PhotoReviewTests, cls).setUpClass()
        storage = FileSystemStorage()
        desired_storage_path = join('queued-images', 'pilot.jpg')
        with open(cls.example_image_filename, 'rb') as f:
            cls.storage_filename = storage.save(desired_storage_path, f)
        mkdir_p(TEST_MEDIA_ROOT)

    @classmethod
    def tearDownClass(cls):
        rmtree(TEST_MEDIA_ROOT)
        super(PhotoReviewTests, cls).tearDownClass()

    def setUp(self):
        super(PhotoReviewTests, self).setUp()
        person_2009 = PersonExtraFactory.create(
            base__id='2009',
            base__name='Tessa Jowell'
        )
        person_2007 = PersonExtraFactory.create(
            base__id='2007',
            base__name='Tessa Jowell'
        )
        CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_2009.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base
            )
        CandidacyExtraFactory.create(
            election=self.election,
            base__person=person_2007.base,
            base__post=self.dulwich_post_extra.base,
            base__on_behalf_of=self.labour_party_extra.base
            )

        self.site = Site.objects.create(domain='example.com', name='YNR')
        self.test_upload_user = User.objects.create_user(
            'john',
            'john@example.com',
            'notagoodpassword',
        )
        self.test_upload_user.terms_agreement.assigned_to_dc = True
        self.test_upload_user.terms_agreement.save()
        self.test_reviewer = User.objects.create_superuser(
            'jane',
            'jane@example.com',
            'alsonotagoodpassword',
        )
        self.test_reviewer.terms_agreement.assigned_to_dc = True
        self.test_reviewer.terms_agreement.save()
        self.test_reviewer.groups.add(
            Group.objects.get(name=PHOTO_REVIEWERS_GROUP_NAME)
        )
        self.q1 = QueuedImage.objects.create(
            why_allowed='public-domain',
            justification_for_use="It's their Twitter avatar",
            decision='undecided',
            image=self.storage_filename,
            person=person_2009.base,
            user=self.test_upload_user
        )
        self.q2 = QueuedImage.objects.create(
            why_allowed='copyright-assigned',
            justification_for_use="I took this last week",
            decision='approved',
            image=self.storage_filename,
            person=person_2007.base,
            user=self.test_upload_user
        )
        self.q3 = QueuedImage.objects.create(
            why_allowed='other',
            justification_for_use="I found it somewhere",
            decision='rejected',
            image=self.storage_filename,
            person=person_2007.base,
            user=self.test_reviewer
        )

    def tearDown(self):
        self.q1.delete()
        self.q2.delete()
        self.q3.delete()
        self.test_upload_user.delete()
        self.test_reviewer.delete()
        self.site.delete()
        super(PhotoReviewTests, self).tearDown()

    def test_photo_upload(self):
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
        form = form_page_response.forms['person-upload-photo']
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

    def test_photo_review_queue_view_not_logged_in(self):
        queue_url = reverse('photo-review-list')
        response = self.app.get(queue_url)
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual('/accounts/login/', split_location.path)
        self.assertEqual('next=/moderation/photo/review', split_location.query)

    def test_photo_review_queue_view_logged_in_unprivileged(self):
        queue_url = reverse('photo-review-list')
        response = self.app.get(
            queue_url,
            user=self.test_upload_user,
            expect_errors=True,
        )
        self.assertEqual(response.status_code, 403)

    def test_photo_review_queue_view_logged_in_privileged(self):
        queue_url = reverse('photo-review-list')
        response = self.app.get(queue_url, user=self.test_reviewer)
        self.assertEqual(response.status_code, 200)
        queue_table = response.html.find('table')
        photo_rows = queue_table.find_all('tr')
        self.assertEqual(2, len(photo_rows))
        cells = photo_rows[1].find_all('td')
        self.assertEqual(cells[1].text, 'john')
        self.assertEqual(cells[2].text, '2009')
        a = cells[3].find('a')
        link_text = re.sub(r'\s+', ' ', a.text).strip()
        link_url = a['href']
        self.assertEqual(link_text, 'Review')
        self.assertEqual(link_url, '/moderation/photo/review/{0}'.format(self.q1.id))

    def test_photo_review_view_unprivileged(self):
        review_url = reverse(
            'photo-review',
            kwargs={'queued_image_id': self.q1.id}
        )
        response = self.app.get(
            review_url,
            user=self.test_upload_user,
            expect_errors=True
        )
        self.assertEqual(response.status_code, 403)

    def test_photo_review_view_privileged(self):
        review_url = reverse(
            'photo-review',
            kwargs={'queued_image_id': self.q1.id}
        )
        response = self.app.get(review_url, user=self.test_reviewer)
        self.assertEqual(response.status_code, 200)
        # For the moment this is just a smoke test...

    @patch('moderation_queue.views.send_mail')
    def test_photo_review_upload_approved_privileged(
            self,
            mock_send_mail
    ):
        settings = get_current_usersettings()
        settings.DEFAULT_FROM_EMAIL = 'admins@example.com'
        settings.site_id = self.site.id
        settings.save()
        with self.settings(SITE_ID=self.site.id):
            review_url = reverse(
                'photo-review',
                kwargs={'queued_image_id': self.q1.id}
            )
            review_page_response = self.app.get(
                review_url,
                user=self.test_reviewer
            )
            form = review_page_response.forms['photo-review-form']
            form['decision'] = 'approved'
            form['moderator_why_allowed'] = 'profile-photo'
            response = form.submit(user=self.test_reviewer)
            # FIXME: check that mocked_person_put got the right calls
            self.assertEqual(response.status_code, 302)
            split_location = urlsplit(response.location)
            self.assertEqual('/moderation/photo/review', split_location.path)

            mock_send_mail.assert_called_once_with(
                'YNR image upload approved',
                "Thank-you for submitting a photo to YNR; that's been uploaded\nnow for the candidate page here:\n\n  http://localhost:80/person/2009/tessa-jowell\n\nMany thanks from the YNR volunteers\n",
                'admins@example.com',
                ['john@example.com'],
                fail_silently=False
            )

            person = Person.objects.get(id=2009)
            image = person.extra.images.last()

            self.assertTrue(image.is_primary)
            self.assertEqual(
                'Uploaded by john: Approved from photo moderation queue',
                image.source
            )
            self.assertEqual(427, image.image.width)
            self.assertEqual(639, image.image.height)

            self.q1.refresh_from_db()
            self.assertEqual('public-domain', self.q1.why_allowed)
            self.assertEqual('approved', self.q1.decision)
            las = LoggedAction.objects.all()
            self.assertEqual(1, len(las))
            la = las[0]
            self.assertEqual(la.user.username, 'jane')
            self.assertEqual(la.action_type, 'photo-approve')
            self.assertEqual(la.person.id, 2009)

            self.assertEqual(QueuedImage.objects.get(pk=self.q1.id).decision, 'approved')

    @patch('moderation_queue.views.send_mail')
    def test_photo_review_upload_rejected_privileged(
            self,
            mock_send_mail
    ):
        settings = get_current_usersettings()
        settings.DEFAULT_FROM_EMAIL = 'admins@example.com'
        settings.SUPPORT_EMAIL = 'support@example.com'
        settings.site_id = self.site.id
        settings.save()
        with self.settings(SITE_ID=self.site.id):
            review_url = reverse(
                'photo-review',
                kwargs={'queued_image_id': self.q1.id}
            )
            review_page_response = self.app.get(
                review_url,
                user=self.test_reviewer
            )
            form = review_page_response.forms['photo-review-form']
            form['decision'] = 'rejected'
            form['rejection_reason'] = 'There\'s no clear source or copyright statement'
            response = form.submit(user=self.test_reviewer)
            self.assertEqual(response.status_code, 302)
            split_location = urlsplit(response.location)
            self.assertEqual('/moderation/photo/review', split_location.path)

            las = LoggedAction.objects.all()
            self.assertEqual(1, len(las))
            la = las[0]
            self.assertEqual(la.user.username, 'jane')
            self.assertEqual(la.action_type, 'photo-reject')
            self.assertEqual(la.person.id, 2009)
            self.assertEqual(la.source, 'Rejected a photo upload from john')
            self.assertEqual(la.note, 'There\'s no clear source or copyright statement')

            mock_send_mail.assert_called_once_with(
                'YNR image moderation results',
                "Thank-you for uploading a photo of Tessa Jowell to YNR, but\nunfortunately we can't use that image because:\n\n  There\'s no clear source or copyright statement\n\nYou can just reply to this email if you want to discuss that\nfurther, or you can try uploading a photo with a different\nreason or justification for its use using this link:\n\n  http://localhost:80/moderation/photo/upload/2009\n\nMany thanks from the YNR volunteers\n\n-- \nFor administrators' use: http://localhost:80/moderation/photo/review/{0}\n".format(self.q1.id),
                'admins@example.com',
                ['john@example.com', 'support@example.com'],
                fail_silently=False
            )

            self.assertEqual(QueuedImage.objects.get(pk=self.q1.id).decision, 'rejected')

    @patch('moderation_queue.views.send_mail')
    def test_photo_review_upload_undecided_privileged(
            self,
            mock_send_mail
    ):
        settings = get_current_usersettings()
        settings.DEFAULT_FROM_EMAIL = 'admins@example.com'
        settings.save()
        review_url = reverse(
            'photo-review',
            kwargs={'queued_image_id': self.q1.id}
        )
        review_page_response = self.app.get(
            review_url,
            user=self.test_reviewer
        )
        form = review_page_response.forms['photo-review-form']
        form['decision'] = 'undecided'
        form['rejection_reason'] = 'No clear source or copyright statement'
        response = form.submit(user=self.test_reviewer)
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual('/moderation/photo/review', split_location.path)

        self.assertEqual(mock_send_mail.call_count, 0)

        self.assertEqual(QueuedImage.objects.get(pk=self.q1.id).decision, 'undecided')

    @patch('moderation_queue.views.send_mail')
    def test_photo_review_upload_ignore_privileged(
            self,
            mock_send_mail
    ):
        settings = get_current_usersettings()
        settings.DEFAULT_FROM_EMAIL = 'admins@example.com'
        settings.save()
        review_url = reverse(
            'photo-review',
            kwargs={'queued_image_id': self.q1.id}
        )
        review_page_response = self.app.get(
            review_url,
            user=self.test_reviewer
        )
        form = review_page_response.forms['photo-review-form']
        form['decision'] = 'ignore'
        response = form.submit(user=self.test_reviewer)
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual('/moderation/photo/review', split_location.path)

        self.assertEqual(mock_send_mail.call_count, 0)

        self.assertEqual(QueuedImage.objects.get(pk=self.q1.id).decision, 'ignore')

        las = LoggedAction.objects.all()
        self.assertEqual(1, len(las))
        la = las[0]
        self.assertEqual(la.user.username, 'jane')
        self.assertEqual(la.action_type, 'photo-ignore')
        self.assertEqual(la.person.id, 2009)
