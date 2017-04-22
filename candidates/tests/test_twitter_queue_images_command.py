from __future__ import print_function, unicode_literals

from mock import Mock, call, patch
from os.path import dirname, join

from django.core.management import call_command
from django.test import TestCase

from candidates.models import ImageExtra
from moderation_queue.models import QueuedImage
from .auth import TestUserMixin
from .factories import PersonExtraFactory
from .output import capture_output, split_output


@patch('candidates.management.commands.candidates_add_twitter_images_to_queue.requests')
@patch('candidates.management.commands.candidates_add_twitter_images_to_queue.TwitterAPIData')
class TestTwitterImageQueueCommand(TestUserMixin, TestCase):

    def setUp(self):
        self.image_filename = join(
            dirname(__file__), '..', '..', 'moderation_queue', 'tests',
            'example-image.jpg'
        )

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

        self.p_accepted_image_in_queue = PersonExtraFactory.create(
            base__id='5',
            base__name='Person With An Accepted Image In The Queue').base
        self.existing_accepted_image = self.p_accepted_image_in_queue.queuedimage_set.create(
            decision=QueuedImage.APPROVED,
            user=self.user,
        )
        self.p_accepted_image_in_queue.identifiers.create(
            identifier='1005',
            scheme='twitter')
        # If they've had an image accepted, they'll probably have an
        # Image too, so create that:
        self.image_create_from_queue = ImageExtra.objects.create_from_file(
            self.image_filename,
            'images/person-accepted.jpg',
            base_kwargs={
                'content_object': self.p_accepted_image_in_queue,
                'is_primary': True,
                'source': 'From Flickr, used as an example image',
            },
            extra_kwargs={
                'copyright': 'example-license',
                'uploading_user': self.user,
                'user_notes': 'Here is a photo for you!',
            }
        )

        self.p_existing_image_but_none_in_queue = PersonExtraFactory.create(
            base__id='6',
            base__name='Person With An Existing Image But None In The Queue').base
        self.p_existing_image_but_none_in_queue.identifiers.create(
            identifier='1006',
            scheme='twitter')
        self.image_create_from_queue = ImageExtra.objects.create_from_file(
            self.image_filename,
            'images/person-existing-image.jpg',
            base_kwargs={
                'content_object': self.p_existing_image_but_none_in_queue,
                'is_primary': True,
                'source': 'From Flickr, used as an example image',
            },
            extra_kwargs={
                'copyright': 'example-license',
                'uploading_user': self.user,
                'user_notes': 'Photo from their party page, say',
            }
        )
        self.existing_queued_image_ids = \
            list(QueuedImage.objects.values_list('pk', flat=True))

    def test_command(self, mock_twitter_data, mock_requests):

        mock_twitter_data.return_value.user_id_to_photo_url = {
            '1001': 'https://pbs.twimg.com/profile_images/abc/foo.jpg',
            '1002': 'https://pbs.twimg.com/profile_images/def/bar.jpg',
            '1003': 'https://pbs.twimg.com/profile_images/ghi/baz.jpg',
            '1005': 'https://pbs.twimg.com/profile_images/jkl/quux.jpg',
            '1006': 'https://pbs.twimg.com/profile_images/mno/xyzzy.jpg',
        }

        mock_requests.get.return_value = Mock(content=b'')

        call_command('candidates_add_twitter_images_to_queue')

        new_queued_images = QueuedImage.objects.exclude(
            id__in=self.existing_queued_image_ids)

        self.assertEqual(
            set(c[1] for c in mock_requests.get.mock_calls),
            {
                ('https://pbs.twimg.com/profile_images/abc/foo.jpg',),
                ('https://pbs.twimg.com/profile_images/mno/xyzzy.jpg',),
            }
        )

        self.assertEqual(new_queued_images.count(), 2)
        new_queued_images.get(person=self.p_no_images)
        new_queued_images.get(person=self.p_existing_image_but_none_in_queue)

    def test_multiple_twitter_identifiers(self, mock_twitter_data, mock_requests):
        self.p_no_images.identifiers.create(
            identifier='1001',
            scheme='twitter')

        mock_twitter_data.return_value.user_id_to_photo_url = {
            '1001': 'https://pbs.twimg.com/profile_images/abc/foo.jpg',
            '1002': 'https://pbs.twimg.com/profile_images/def/bar.jpg',
            '1003': 'https://pbs.twimg.com/profile_images/ghi/baz.jpg',
            '1005': 'https://pbs.twimg.com/profile_images/jkl/quux.jpg',
            '1006': 'https://pbs.twimg.com/profile_images/mno/xyzzy.jpg',
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
                '  That person already had an image in the queue, so skipping.',
                'Considering adding a photo for Person With Only Rejected ' \
                'Images In The Queue with Twitter user ID: 1003',
                '  That person already had an image in the queue, so skipping.',
                'Considering adding a photo for Person With An Accepted ' \
                'Image In The Queue with Twitter user ID: 1005',
                '  That person already had an image in the queue, so skipping.',
                'Considering adding a photo for Person With An Existing ' \
                'Image But None In The Queue with Twitter user ID: 1006',
                '  Adding that person\'s Twitter avatar to the moderation ' \
                'queue'
            ]
        )

        new_queued_images = QueuedImage.objects.exclude(
            id__in=self.existing_queued_image_ids)

        self.assertEqual(
            mock_requests.get.mock_calls,
            [
                call('https://pbs.twimg.com/profile_images/mno/xyzzy.jpg'),
            ]
        )

        self.assertEqual(new_queued_images.count(), 1)
        new_queued_images.get(person=self.p_existing_image_but_none_in_queue)
