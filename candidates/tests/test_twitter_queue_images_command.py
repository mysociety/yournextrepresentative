from __future__ import print_function, unicode_literals

from mock import Mock, call, patch

from django.core.management import call_command
from django.test import TestCase

from moderation_queue.models import QueuedImage
from .auth import TestUserMixin
from .factories import PersonExtraFactory
from .output import capture_output, split_output


@patch('candidates.management.commands.candidates_add_twitter_images_to_queue.requests')
@patch('candidates.management.commands.candidates_add_twitter_images_to_queue.TwitterAPIData')
class TestTwitterImageQueueCommand(TestUserMixin, TestCase):

    # Note that these tests test the existing behaviour of the
    # command, which doesn't seem quite right to me. It only considers
    # if there are non-rejected images for the person in the image
    # queue, when perhaps it should also consider if there are any
    # images in person.extra.images.

    def setUp(self):
        self.p_no_images = PersonExtraFactory.create(
            base__id='1',
            base__name='Person With No Existing Images').base
        self.p_no_images.identifiers.create(
            identifier='1001',
            scheme='twitter')

        p_existing_image = PersonExtraFactory.create(
            base__id='2',
            base__name='Person With An Existing Image').base
        self.existing_undecided_image = p_existing_image.queuedimage_set.create(
            decision=QueuedImage.UNDECIDED,
            user=self.user,
        )
        p_existing_image.identifiers.create(
            identifier='1002',
            scheme='twitter')

        self.p_only_rejected_in_queue = PersonExtraFactory.create(
            base__id='3',
            base__name='Person With Only Rejected Images In The Queue').base
        self.existing_rejected_image = self.p_only_rejected_in_queue.queuedimage_set.create(
            decision=QueuedImage.REJECTED,
            user=self.user,
        )
        self.p_only_rejected_in_queue.identifiers.create(
            identifier='1003',
            scheme='twitter')

        PersonExtraFactory.create(
            base__id='4',
            base__name='Person With No Twitter User ID')

        self.existing_queued_image_ids = \
            list(QueuedImage.objects.values_list('pk', flat=True))

    def test_command(self, mock_twitter_data, mock_requests):

        mock_twitter_data.return_value.user_id_to_photo_url = {
            '1001': 'https://pbs.twimg.com/profile_images/abc/foo.jpg',
            '1002': 'https://pbs.twimg.com/profile_images/def/bar.jpg',
            '1003': 'https://pbs.twimg.com/profile_images/ghi/baz.jpg',
        }

        mock_requests.get.return_value = Mock(content=b'')

        call_command('candidates_add_twitter_images_to_queue')

        new_queued_images = QueuedImage.objects.exclude(
            id__in=self.existing_queued_image_ids)

        self.assertEqual(
            mock_requests.get.mock_calls,
            [
                call('https://pbs.twimg.com/profile_images/abc/foo.jpg'),
                call('https://pbs.twimg.com/profile_images/ghi/baz.jpg'),
            ]
        )

        self.assertEqual(new_queued_images.count(), 2)
        new_queued_images.get(person=self.p_no_images)
        new_queued_images.get(person=self.p_only_rejected_in_queue)

    def test_multiple_twitter_identifiers(self, mock_twitter_data, mock_requests):
        self.p_no_images.identifiers.create(
            identifier='1001',
            scheme='twitter')

        mock_twitter_data.return_value.user_id_to_photo_url = {
            '1001': 'https://pbs.twimg.com/profile_images/abc/foo.jpg',
            '1002': 'https://pbs.twimg.com/profile_images/def/bar.jpg',
            '1003': 'https://pbs.twimg.com/profile_images/ghi/baz.jpg',
        }

        mock_requests.get.return_value = Mock(content=b'')

        with capture_output() as (out, err):
            call_command('candidates_add_twitter_images_to_queue', verbosity=3)

        self.assertEqual(
            split_output(out),
            [
                'WARNING: Multiple Twitter user IDs found for Person ' \
                'With No Existing Images ({0}), skipping'.format(
                    self.p_no_images.id),
                'Considering adding a photo for Person With An Existing ' \
                'Image with Twitter user ID: 1002',
                '  That person already had in image, so skipping.',
                'Considering adding a photo for Person With Only Rejected ' \
                'Images In The Queue with Twitter user ID: 1003',
                '  Adding that person\'s Twitter avatar to the moderation ' \
                'queue'
            ]
        )

        new_queued_images = QueuedImage.objects.exclude(
            id__in=self.existing_queued_image_ids)

        self.assertEqual(
            mock_requests.get.mock_calls,
            [
                call('https://pbs.twimg.com/profile_images/ghi/baz.jpg'),
            ]
        )

        self.assertEqual(new_queued_images.count(), 1)
        new_queued_images.get(person=self.p_only_rejected_in_queue)
