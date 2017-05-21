from __future__ import print_function, unicode_literals

from datetime import datetime
from random import randint
import sys

from django.db import transaction
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext as _

from candidates.models import MultipleTwitterIdentifiers
from popolo.models import Person

from ..twitter import TwitterAPIData


VERBOSE = False


def verbose(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)


class Command(BaseCommand):

    help = "Use the Twitter API to check / fix Twitter screen names and user IDs"

    def record_new_version(self, person, msg=None):
        if msg is None:
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

    def remove_twitter_screen_name(self, person, twitter_screen_name):
        person.contact_details.get(
            contact_type='twitter',
            value=twitter_screen_name,
        ).delete()
        self.record_new_version(
            person,
            msg="This Twitter screen name no longer exists; removing it " \
            "(candidates_update_twitter_usernames)"
        )

    def remove_twitter_user_id(self, person, twitter_user_id):
        person.identifiers.get(
            scheme='twitter',
            identifier=twitter_user_id,
        ).delete()
        self.record_new_version(
            person,
            msg="This Twitter user ID no longer exists; removing it " \
            "(candidates_update_twitter_usernames)",
        )

    def handle_person(self, person):
        try:
            user_id, screen_name = person.extra.twitter_identifiers
        except MultipleTwitterIdentifiers as e:
            print(u"WARNING: {message}, skipping".format(message=e))
            return
        # If they have a Twitter user ID, then check to see if we
        # need to update the screen name from that; if so, update
        # the screen name.  Skip to the next person. This catches
        # people who have changed their Twitter screen name, or
        # anyone who had a user ID set but not a screen name
        # (which should be rare).  If the user ID is not a valid
        # Twitter user ID, it is deleted.
        if user_id:
            verbose(_("{person} has a Twitter user ID: {user_id}").format(
                person=person, user_id=user_id
            ))
            if user_id not in self.twitter_data.user_id_to_screen_name:
                print(_("Removing user ID {user_id} for {person_name} as it is not a valid Twitter user ID. {person_url}").format(
                    user_id=user_id,
                    person_name=person.name,
                    person_url=person.extra.get_absolute_url(),
                ))
                self.remove_twitter_user_id(person, user_id)
                if screen_name:
                    self.remove_twitter_screen_name(person, screen_name)
                return
            correct_screen_name = self.twitter_data.user_id_to_screen_name[user_id]
            if (screen_name is None) or (screen_name != correct_screen_name):
                print(_("Correcting the screen name from {old_screen_name} to {correct_screen_name}").format(
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

        # Otherwise, if they have a Twitter screen name (but no
        # user ID, since we already dealt with that case) then
        # find their Twitter user ID and set that as an identifier.
        # If the screen name is not a valid Twitter screen name, it
        # is deleted.
        elif screen_name:
            verbose(_("{person} has Twitter screen name ({screen_name}) but no user ID").format(
                person=person, screen_name=screen_name
            ))
            if screen_name.lower() not in self.twitter_data.screen_name_to_user_id:
                print(_("Removing screen name {screen_name} for {person_name} as it is not a valid Twitter screen name. {person_url}").format(
                    screen_name=screen_name,
                    person_name=person.name,
                    person_url=person.extra.get_absolute_url(),
                ))
                self.remove_twitter_screen_name(person, screen_name)
                return
            print(_("Adding the user ID {user_id}").format(
                user_id=self.twitter_data.screen_name_to_user_id[screen_name.lower()]
            ))
            person.identifiers.create(
                scheme='twitter',
                identifier=self.twitter_data.screen_name_to_user_id[screen_name.lower()]
            )
            self.record_new_version(person)
        else:
            verbose(_("{person} had no Twitter account information").format(
                person=person
            ))

    def handle(self, *args, **options):
        global VERBOSE
        VERBOSE = int(options['verbosity']) > 1
        self.twitter_data = TwitterAPIData()
        self.twitter_data.update_from_api()
        # Now go through every person in the database and check their
        # Twitter details. This can take a long time, so use one
        # transaction per person.
        for person_id in Person.objects.order_by('name').values_list('pk', flat=True):
            with transaction.atomic():
                # n.b. even though it's inefficient query-wise, we get
                # each person from the database based on their ID
                # within the transaction because the loop we're in
                # takes a long time, other otherwise we might end up
                # with out of date information (e.g. this has happened
                # with the person.extra.versions field, with confusing
                # results...)
                person = Person.objects.select_related('extra').get(pk=person_id)
                self.handle_person(person)
