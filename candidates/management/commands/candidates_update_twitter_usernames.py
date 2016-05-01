from __future__ import print_function, unicode_literals

from datetime import datetime
from random import randint
import sys

from django.db import transaction
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _
from django.utils.six import text_type
from django.core.files.temp import NamedTemporaryFile
from django.core.files import File

from popolo.models import ContactDetail, Identifier, Person
from moderation_queue.models import QueuedImage, CopyrightOptions
import requests

MAX_IN_A_REQUEST = 100
VERBOSE = False


def verbose(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)


class Command(BaseCommand):

    help = "Use the Twitter API to check / fix Twitter screen names and user IDs"

    def record_new_version(self, person):
        msg = 'Updated by the automated Twitter account checker ' \
              '(candidates_update_twitter_usernames)'
        person.extra.record_version(
            {
                'information_source': msg,
                'version_id': "{0:016x}".format(randint(0, sys.maxsize)),
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        person.extra.save()

    def add_twitter_image_to_queue(self, person, image_url):
        if person.queuedimage_set.exclude(decision="rejected").exists():
            # Don't add an image to the queue if there is one already
            # Ignoring rejected queued images
            return

        # Add a new queued image
        image_url = image_url.replace('_normal.', '.')
        img_temp = NamedTemporaryFile(delete=True)
        img_temp.write(requests.get(image_url).content)
        img_temp.flush()

        qi = QueuedImage(
            decision=QueuedImage.UNDECIDED,
            why_allowed=CopyrightOptions.PROFILE_PHOTO,
            justification_for_use="Auto imported from Twitter",
            person=person
        )
        qi.save()
        qi.image.save(image_url, File(img_temp))
        qi.save()


    def handle_person(self, person):
        # Get the Twitter screen name and user ID if they exist:
        try:
            screen_name = person.contact_details \
                .get(contact_type='twitter').value
        except ContactDetail.DoesNotExist:
            screen_name = None
        try:
            user_id = person.identifiers \
                .get(scheme='twitter').identifier
        except Identifier.DoesNotExist:
            user_id = None
        # If they have a Twitter user ID, then check to see if we
        # need to update the screen name from that; if so, update
        # the screen name.  Skip to the next person. This catches
        # people who have changed their Twitter screen name, or
        # anyone who had a user ID set but not a screen name
        # (which should be rare).
        if user_id:
            verbose(_("{person} has a Twitter user ID: {user_id}").format(
                person=person, user_id=user_id
            ))
            if user_id not in self.user_id_to_screen_name:
                print(_("Warning: user ID {user_id} not found for {person_name}: {person_url}").format(
                    user_id=user_id,
                    person_name=person.name,
                    person_url=person.extra.get_absolute_url(),
                ))
                return
            correct_screen_name = self.user_id_to_screen_name[user_id]
            if (screen_name is None) or (screen_name != correct_screen_name):
                verbose(_("Correcting the screen name from {old_screen_name} to {correct_screen_name}").format(
                    old_screen_name=screen_name,
                    correct_screen_name=correct_screen_name
                ))
                person.contact_details.update_or_create(
                    contact_type='twitter',
                    defaults={'value': correct_screen_name},
                )
                self.record_new_version(person)
            else:
                verbose(_("The screen name ({screen_name}) was already correct").format(
                    screen_name=screen_name
                ))

            if user_id in self.user_id_to_photo_url:
                self.add_twitter_image_to_queue(
                    person, self.user_id_to_photo_url[user_id])
        # Otherwise, if they have a Twitter screen name (but no
        # user ID, since we already dealt with that case) then
        # find their Twitter user ID and set that as an identifier.
        elif screen_name:
            verbose(_("{person} has Twitter screen name ({screen_name}) but no user ID").format(
                person=person, screen_name=screen_name
            ))
            if screen_name.lower() not in self.screen_name_to_user_id:
                print(_("Warning: screen name {screen_name} not found for {person_name}: {person_url}").format(
                    screen_name=screen_name,
                    person_name=person.name,
                    person_url=person.extra.get_absolute_url(),
                ))
                return
            verbose(_("Adding the user ID {user_id}").format(
                user_id=self.screen_name_to_user_id[screen_name.lower()]
            ))
            person.identifiers.create(
                scheme='twitter',
                identifier=self.screen_name_to_user_id[screen_name.lower()]
            )
            self.record_new_version(person)
        else:
            verbose(_("{person} had no Twitter account information").format(
                person=person
            ))

    def handle(self, *args, **options):
        global VERBOSE
        VERBOSE = int(options['verbosity']) > 1
        token = settings.TWITTER_APP_ONLY_BEARER_TOKEN
        if not token:
            raise CommandError(_("TWITTER_APP_ONLY_BEARER_TOKEN was not set"))
        headers = {'Authorization': 'Bearer {token}'.format(token=token)}

        # Find all unique Twitter screen names in the database:
        all_screen_names = list(
            ContactDetail.objects.filter(contact_type='twitter'). \
                values_list('value', flat=True).distinct()
        )

        # Find all unique Twitter identifiers in the database:
        all_user_ids = list(
            Identifier.objects.filter(scheme='twitter'). \
                values_list('identifier', flat=True).distinct()
        )

        self.screen_name_to_user_id = {}
        self.user_id_to_screen_name = {}
        self.user_id_to_photo_url = {}
        for i in range(0, len(all_screen_names), MAX_IN_A_REQUEST):
            screen_names = all_screen_names[i:(i + MAX_IN_A_REQUEST)]
            r = requests.post(
                'https://api.twitter.com/1.1/users/lookup.json',
                data={
                    'screen_name': ','.join(screen_names)
                },
                headers=headers,
            )
            for d in r.json():
                user_id = text_type(d['id'])
                self.screen_name_to_user_id[d['screen_name'].lower()] = user_id
                self.user_id_to_screen_name[user_id] = d['screen_name']
                self.user_id_to_photo_url[user_id] = \
                    d['profile_image_url_https']


        # Now look for any user IDs in the database that weren't found
        # from the above query:
        remaining_user_ids = list(
            set(all_user_ids) - set(self.user_id_to_screen_name.keys())
        )
        for i in range(0, len(remaining_user_ids), MAX_IN_A_REQUEST):
            user_ids = remaining_user_ids[i:(i + MAX_IN_A_REQUEST)]
            r = requests.post(
                'https://api.twitter.com/1.1/users/lookup.json',
                data={
                    'user_id': ','.join(user_ids)
                },
                headers=headers,
            )
            for d in r.json():
                user_id = text_type(d['id'])
                self.screen_name_to_user_id[d['screen_name'].lower()] = user_id
                self.user_id_to_screen_name[user_id] = d['screen_name']
                self.user_id_to_photo_url[user_id] = \
                    d['profile_image_url_https']
        # Now go through every person in the database and check their
        # Twitter details:
        for person in Person.objects.select_related('extra'):
            with transaction.atomic():
                self.handle_person(person)
