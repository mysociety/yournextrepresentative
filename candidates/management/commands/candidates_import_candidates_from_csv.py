import csv
from datetime import datetime
from random import randint
import sys


from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from elections.models import Election
from popolo import models as pmodels
from candidates import models
from candidates.models.field_mappings import form_complex_fields_locations


def tidy_row(row):
    return {
        k.strip(): v.strip().decode('utf-8')
        for k, v in row.items()
    }


class Command(BaseCommand):
    help = 'Create or update candidates from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('ELECTION-SLUG')
        parser.add_argument('CSV-FILE')

    def get_party(self, row):
        party_id = row.get('Party ID')
        party_name = row.get('Party Name')
        if not (party_id or party_name):
            msg = "There must be either a 'Party ID' or 'Party Name' column"
            raise CommandError(msg)
        if party_id:
            try:
                party = pmodels.Organization.objects \
                    .select_related('extra') \
                    .get(extra__slug=party_id)
            except pmodels.Organization.DoesNotExist:
                msg = "No party found with ID '{0}'"
                raise CommandError(msg.format(party_id))
        else:
            try:
                party = pmodels.Organization.objects.get(name__iexact=party_name)
            except pmodels.Organization.DoesNotExist:
                msg = u"No party found with name '{0}'"
                raise CommandError(msg.format(party_name))
        return party

    def get_post(self, row):
        post_id = row.get('Post ID')
        post_label = row.get('Post Label')
        if not (post_id or post_label):
            msg = "There must be either a 'Post ID' or 'Post Label' column"
            raise CommandError(msg)
        if post_id:
            try:
                post = pmodels.Post.objects \
                    .select_related('extra') \
                    .get(extra__slug=post_id)
            except pmodels.Post.DoesNotExist:
                msg = "No post found with ID '{0}'"
                raise CommandError(msg.format(post_id))
        else:
            try:
                post = pmodels.Post.objects.get(label__iexact=post_label)
            except pmodels.Organization.DoesNotExist:
                msg = u"No post found with label '{0}'"
                raise CommandError(msg.format(post_label))
        return post

    def add_candidate(self, election, row, **options):
        name = row['Name']
        print "Adding:", name
        party = self.get_party(row)
        post = self.get_post(row)
        person = pmodels.Person.objects.create(name=name)
        person_extra = models.PersonExtra.objects.create(base=person)
        # The 'simple' fields:
        for csv_header, simple_field in (
                ('Email', 'email'),
                ('Gender', 'gender'),
                ('DOB', 'birth_date'),
                ('Honorific Prefix', 'honorific_prefix'),
                ('Honorific Suffix', 'honorific_suffix'),
        ):
            if row.get(csv_header):
                setattr(person, simple_field, row[csv_header])
        person.save()
        # The 'complex' fields:
        for csv_header, complex_field in (
                ('Twitter', 'twitter_username'),
                ('Homepage', 'homepage_url'),
                ('Wikipedia', 'wikipedia_url'),
                ('LinkedIn', 'linkedin_url'),
                ('Facebook Personal', 'facebook_personal_url'),
                ('Facebook Page', 'facebook_page_url'),
        ):
            if row.get(csv_header):
                location = form_complex_fields_locations[complex_field]
                person_extra.update_complex_field(location, row[csv_header])
        person_extra.record_version(
            {
                'information_source': 'New candidate imported from CSV',
                'version_id': "{0:016x}".format(randint(0, sys.maxint)),
                'timestamp': datetime.utcnow().isoformat(),
            }
        )
        membership = pmodels.Membership.objects.create(
            on_behalf_of=party,
            person=person,
            post=post,
            role=election.candidate_membership_role,
        )
        membership_extra = models.MembershipExtra(
            base=membership,
            election=election,
        )
        if row.get('Party List Position'):
            membership_extra.party_list_position = row['Party List Position']
        membership_extra.save()
        person_extra.save()

    def handle(self, **options):
        with transaction.atomic():
            election_slug = options['ELECTION-SLUG']
            try:
                election = Election.objects.get(slug=election_slug)
            except Election.DoesNotExist:
                msg = "No election found with the slug '{0}'"
                raise CommandError(msg.format())
            with open(options['CSV-FILE'], 'rb') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row = tidy_row(row)
                    self.add_candidate(election, row, **options)
