from datetime import date
import json
import sys

from slugify import slugify

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.urlresolvers import reverse
from django.db import connection
from django.db import models
from django.utils.translation import ugettext as _

from elections.models import Election
from popolo.models import Person, Organization, Post, Membership
from .field_mappings import (
    form_simple_fields, form_complex_fields_locations
)
from .popit import parse_approximate_date
from .versions import get_person_as_version_data

from images.models import Image, HasImageMixin

"""Extensions to the base django-popolo classes for YourNextRepresentative

These are done via explicit one-to-one fields to avoid the performance
problems with multi-table inheritance; it's preferable to state when you
want a join or not.

  http://stackoverflow.com/q/23466577/223092

"""


class PersonExtra(HasImageMixin, models.Model):
    base = models.OneToOneField(Person, related_name='extra')

    # These two fields are added just for Burkina Faso - we should
    # have a better way of adding arbitrary fields which are only
    # needed for one site.
    cv = models.TextField(blank=True)
    program = models.TextField(blank=True)

    # This field stores JSON data with previous version information
    # (as it did in PopIt).
    versions = models.TextField(blank=True)

    images = GenericRelation(Image)

    def __getattr__(self, name):
        if name in form_complex_fields_locations:
            loc = form_complex_fields_locations[name]
            # Iterate rather than using filter because that would
            # cause an extra query when the relation has already been
            # populated via select_related:
            for e in getattr(self.base, loc['sub_array']).all():
                if getattr(e, loc['info_type_key']) == loc['info_type']:
                    return getattr(e, loc['info_value_key'])
            return None
        else:
            message = _("'PersonExtra' object has no attribute '{name}'")
            raise AttributeError(message.format(name=name))

    def get_slug(self):
        return slugify(self.base.name)

    def get_absolute_url(self, request=None):
        path = reverse(
            'person-view',
            kwargs={
                'person_id': self.base.id,
                'ignored_slug': self.get_slug(),
            }
        )
        if request is None:
            return path
        return request.build_absolute_uri(path)

    @property
    def last_candidacy(self):
        ordered_candidacies = Membership.objects. \
            filter(person=self.base, extra__election__isnull=False). \
            order_by('extra__election__election_date')
        return ordered_candidacies.last()

    @property
    def proxy_image(self):
        # raise NotImplementedError()
        return "foo"

    @property
    def image(self):
        raise NotImplementedError()

    def name_with_honorifics(self):
        name_parts = []
        pre = self.base.honorific_prefix
        post = self.base.honorific_suffix
        if pre:
            name_parts.append(pre)
        name_parts.append(self.base.name)
        if post:
            name_parts.append(post)
        return ' '.join(name_parts)

    @property
    def dob_as_approximate_date(self):
        return parse_approximate_date(self.base.birth_date)

    def dob_as_date(self):
        approx = self.dob_as_approximate_date
        return date(approx.year, approx.month, approx.day)

    @property
    def age(self):
        """Return a string representing the person's age"""

        dob = self.dob_as_approximate_date
        if not dob:
            return None
        today = date.today()
        approx_age = today.year - dob.year
        if dob.month == 0 and dob.day == 0:
            min_age = approx_age - 1
            max_age = approx_age
        elif dob.day == 0:
            min_age = approx_age - 1
            max_age = approx_age
            if today.month < dob.month:
                max_age = min_age
            elif today.month > dob.month:
                min_age = max_age
        else:
            # There's a complete date:
            dob_as_date = self.dob_as_date()
            try:
                today_in_birth_year = date(dob.year, today.month, today.day)
            except ValueError:
                # It must have been February 29th
                today_in_birth_year = date(dob.year, 3, 1)
            if today_in_birth_year > dob_as_date:
                min_age = max_age = today.year - dob.year
            else:
                min_age = max_age = (today.year - dob.year) -1
        if min_age == max_age:
            # We know their exact age:
            return str(min_age)
        return "{0} or {1}".format(min_age, max_age)

    def get_elected(self, election_slug):
        election = Election.objects.get_by_slug(election_slug)
        return self.base.memberships.filter(
            role=election.winner_membership_role,
            organization_id=election.organization_id
        ).exists()

    def last_party(self):
        party = self.base.memberships.filter(
            organization__classification='Party'
        ).order_by('start_date').last()

        return party.organization

    @classmethod
    def get_max_person_id(cls):
        cursor = connection.cursor()
        cursor.execute('SELECT MAX(CAST (id AS int)) FROM popolo_person')
        max_id = cursor.fetchone()[0]
        if max_id is None:
            return 0
        return max_id

    def record_version(self, change_metadata):
        versions = []
        if self.versions:
            versions = json.loads(self.versions)
        new_version = change_metadata.copy()
        new_version['data'] = get_person_as_version_data(self.base)
        versions.insert(0, new_version)
        self.versions = versions

    def update_complex_field(self, location, new_value):
        existing_info_types = [location['info_type']]
        if 'old_info_type' in location:
            existing_info_types.append(location['old_info_type'])
        related_manager = getattr(self.base, location['sub_array'])
        # Remove the old entries of that type:
        kwargs = {
            (location['info_type_key'] + '__in'): existing_info_types
        }
        related_manager.filter(**kwargs).delete()
        if new_value:
            kwargs = {
                location['info_type_key']: location['info_type'],
                location['info_value_key']: new_value,
            }
            related_manager.create(**kwargs)

    @classmethod
    def create_from_form(cls, form):
        form_data = form.cleaned_data.copy()
        # The date is returned as a datetime.date, so if that's set, turn
        # it into a string:
        birth_date_date = form_data['birth_date']
        if birth_date_date:
            form_data['birth_date'] = repr(birth_date_date).replace("-00-00", "")
        else:
            form_data['birth_date'] = ''
        # Now set the simple fields:
        kwargs = {
            k: form_data[k]
            for k in form_simple_fields.keys()
        }
        kwargs['id'] = cls.get_max_person_id() + 1
        person = Person.objects.create(**kwargs)
        kwargs = {
            k: form_data[k]
            for k in settings.EXTRA_SIMPLE_FIELDS.keys()
        }
        kwargs['base'] = person
        person_extra = cls.objects.create(**kwargs)
        # Set the 'complex' fields:
        for field_name, location in form_complex_fields_locations.items():
            person_extra.update_complex_field(location, form_data[field_name])
        # Memberships to create:
        for election in form.elections_with_fields:
            post_id = form_data.get('constituency_' + election.slug)
            if not post_id:
                continue
            from candidates.election_specific import AREA_POST_DATA
            party_set = AREA_POST_DATA.post_id_to_party_set(post_id)
            party_key = 'party_' + party_set + '_' + election.slug
            position_key = \
                'party_list_position_' + party_set + '_' + election.slug
            post = Post.objects.get(id=post_id)
            # Get information for this election from the form:
            standing = \
                form_data.pop('standing_' + election.slug, 'standing')
            party = Organization.objects.get(pk=form_data[party_key])
            party_list_position = form_data.get(position_key) or None
            if standing == 'standing':
                membership = Membership.objects.create(
                    post=post,
                    on_behalf_of=party,
                    person=person,
                    role=election.candidate_membership_role,
                )
                MembershipExtra.objects.create(
                    base=membership,
                    party_list_position=party_list_position,
                    election=election
                )
            else:
                # Otherwise remove that person's memberships on this post:
                for m in MembershipExtra.objects.filter(
                        election=election,
                        base__person=person,
                ):
                    # This cascades to delete the base as well:
                    m.delete()
        return person_extra


class OrganizationExtra(models.Model):
    base = models.OneToOneField(Organization, related_name='extra')

    # For parties, which party register is it on:
    register = models.CharField(blank=True, max_length=512)

    images = GenericRelation(Image)


class PostExtra(HasImageMixin, models.Model):
    base = models.OneToOneField(Post, related_name='extra')

    candidates_locked = models.BooleanField(default=False)
    elections = models.ManyToManyField(Election, related_name='posts')

    @property
    def short_label(self):
        from candidates.election_specific import AREA_POST_DATA
        return AREA_POST_DATA.shorten_post_label(self.base.label)


class MembershipExtra(models.Model):
    base = models.OneToOneField(Membership, related_name='extra')

    party_list_position = models.IntegerField(null=True)
    election = models.ForeignKey(
        Election, blank=True, null=True, related_name='candidacies'
    )
