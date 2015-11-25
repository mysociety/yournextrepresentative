from datetime import date
import json

from slugify import slugify

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.core.urlresolvers import reverse
from django.db import connection
from django.db import models
from django.utils.translation import ugettext as _

from elections.models import Election, AreaType
from popolo.models import Person, Organization, Post, Membership, Area
from ..diffs import get_version_diffs
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

def update_person_from_form(person, person_extra, form):
    form_data = form.cleaned_data.copy()
    # The date is returned as a datetime.date, so if that's set, turn
    # it into a string:
    birth_date_date = form_data['birth_date']
    if birth_date_date:
        form_data['birth_date'] = repr(birth_date_date).replace("-00-00", "")
    else:
        form_data['birth_date'] = ''
    for field_name in form_simple_fields.keys():
        setattr(person, field_name, form_data[field_name])
    for field_name in settings.EXTRA_SIMPLE_FIELDS.keys():
        setattr(person_extra, field_name, form_data[field_name])
    for field_name, location in form_complex_fields_locations.items():
        person_extra.update_complex_field(location, form_data[field_name])
    person.save()
    person_extra.save()
    for election_data in form.elections_with_fields:
        post_id = form_data.get('constituency_' + election_data.slug)
        standing = form_data.pop('standing_' + election_data.slug, 'standing')
        if post_id:
            party_set = PartySet.objects.get(postextra__slug=post_id)
            party_key = 'party_' + party_set.slug + '_' + election_data.slug
            position_key = \
                'party_list_position_' + party_set.slug + '_' + election_data.slug
            party = Organization.objects.get(pk=form_data[party_key])
            party_list_position = form_data.get(position_key) or None
            post = Post.objects.get(extra__slug=post_id)
        else:
            party = None
            party_list_position = None

        # Remove any existing memberships; we'll recreate them if the
        # person's actually standing. (Since MembershipExtra depends
        # on Membership, this will delete any corresponding Membership.)
        Membership.objects.filter(
            extra__election=election_data,
            role=election_data.candidate_membership_role,
            person__extra=person_extra
        ).delete()

        if standing == 'standing':
            # Create the new membership:
            membership = Membership.objects.create(
                post=post,
                on_behalf_of=party,
                person=person,
                role=election_data.candidate_membership_role,
            )
            MembershipExtra.objects.create(
                base=membership,
                party_list_position=party_list_position,
                election=election_data
            )


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
            return ''
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
    def current_candidacies(self):
        result = self.base.memberships.filter(
            extra__election__current=True,
            role=models.F('extra__election__candidate_membership_role')
        ).select_related('person', 'on_behalf_of', 'post') \
            .prefetch_related('post__extra')
        return list(result)

    @property
    def last_candidacy(self):
        ordered_candidacies = Membership.objects. \
            filter(person=self.base, extra__election__isnull=False). \
            order_by('extra__election__election_date')
        return ordered_candidacies.last()

    def standing_in(self, election_slug):
        election = Election.objects.get_by_slug(election_slug)
        membership = self.base.memberships.filter(
            role=election.candidate_membership_role,
            extra__election=election
        )
        if membership.exists():
            return membership.first().post
        return None

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

    def get_elected(self, election):
        # FIXME: change this to use the MembershipExtra elected
        # property...
        role = election.winner_membership_role
        if role is None:
            role = ''
        return self.base.memberships.filter(
            role=role,
            organization=election.organization,
            extra__election=election,
            extra__elected=True
        ).exists()

    def last_party(self):
        party = self.base.memberships.filter(
            organization__classification='Party'
        ).order_by('start_date').last()

        if party is not None:
            return party.organization

        return None

    @property
    def version_diffs(self):
        versions = self.versions
        if not versions:
            versions = []
        return get_version_diffs(json.loads(versions))

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
        self.versions = json.dumps(versions)

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

    def get_initial_form_data(self):
        initial_data = {}
        fields_on_base = form_simple_fields.keys()
        fields_on_extra = settings.EXTRA_SIMPLE_FIELDS.keys()
        fields_on_extra += form_complex_fields_locations.keys()
        for field_name in fields_on_base:
            initial_data[field_name] = getattr(self.base, field_name)
        for field_name in fields_on_extra:
            initial_data[field_name] = getattr(self, field_name)
        for election_data in Election.objects.current().by_date():
            constituency_key = 'constituency_' + election_data.slug
            standing_key = 'standing_' + election_data.slug
            try:
                candidacy = MembershipExtra.objects.get(
                    election=election_data,
                    base__person__extra=self
                )
            except MembershipExtra.DoesNotExist:
                candidacy = None
            if candidacy:
                initial_data[standing_key] = 'standing'
                post_id = candidacy.base.post.extra.slug
                initial_data[constituency_key] = post_id
                party_set = PartySet.objects.get(postextra__slug=post_id)
                party = candidacy.base.on_behalf_of
                party_key = 'party_' + party_set.slug + '_' + election_data.slug
                initial_data[party_key] = party.id
                position = candidacy.party_list_position
                position_key = 'party_list_position_' + party_set.slug + '_' + election_data.slug
                if position:
                    initial_data[position_key] = position
            else:
                initial_data[standing_key] = 'not-standing'
                initial_data[constituency_key] = ''
        return initial_data

    def update_from_form(self, form):
        update_person_from_form(self.base, self, form)

    @classmethod
    def create_from_form(cls, form):
        person = Person.objects.create(
            id=(cls.get_max_person_id() + 1),
            name=form.cleaned_data['name'],
        )
        person_extra = PersonExtra.objects.create(
            base=person,
        )
        update_person_from_form(person, person_extra, form)
        return person_extra

    def as_dict(self, election):
        candidacy_extra = MembershipExtra.objects \
            .select_related('base', 'base__post__area') \
            .prefetch_related(
                'base__post__extra',
                'base__on_behalf_of__extra',
                'base__post__area__other_identifiers',
            ) \
            .get(
                election=election,
                base__person=self.base,
                base__role=election.candidate_membership_role,
            )
        party = candidacy_extra.base.on_behalf_of
        post = candidacy_extra.base.post
        elected = self.get_elected(election)
        elected_for_csv = ''
        if elected is not None:
            elected_for_csv = str(elected)
        primary_image_url = ''
        primary_image = self.primary_image()
        if primary_image:
            primary_image_url = primary_image.url()

        row = {
            'id': self.base.id,
            'name': self.base.name,
            'honorific_prefix': self.base.honorific_prefix,
            'honorific_suffix': self.base.honorific_suffix,
            'gender': self.base.gender,
            'birth_date': self.base.birth_date,
            'election': election.slug,
            'party_id': party.extra.slug,
            'party_name': party.name,
            'post_id': post.extra.slug,
            'post_label': post.extra.short_label,
            'mapit_url': post.area.other_identifiers \
                .get(scheme='mapit-area-url').identifier,
            'elected': elected_for_csv,
            'email': self.base.email,
            'twitter_username': self.twitter_username,
            'facebook_page_url': self.facebook_page_url,
            'linkedin_url': self.linkedin_url,
            'party_ppc_page_url': self.party_ppc_page_url,
            'facebook_personal_url': self.facebook_personal_url,
            'homepage_url': self.homepage_url,
            'wikipedia_url': self.wikipedia_url,
            'image_url': primary_image_url,
            # FIXME: we need to find an alternative to the PopIt image
            # proxy:
            'proxy_image_url_template': '',
            # FIXME: add these extra image properties
            # 'image_copyright': image_copyright,
            # 'image_uploading_user': image_uploading_user,
            # 'image_uploading_user_notes': image_uploading_user_notes,
            'image_copyright': '',
            'image_uploading_user': '',
            'image_uploading_user_notes': '',
        }
        from ..election_specific import get_extra_csv_values
        extra_csv_data = get_extra_csv_values(self.base, election)
        row.update(extra_csv_data)

        return row



class OrganizationExtra(models.Model):
    base = models.OneToOneField(Organization, related_name='extra')
    slug = models.CharField(max_length=256, blank=True)

    # For parties, which party register is it on:
    register = models.CharField(blank=True, max_length=512)

    images = GenericRelation(Image)


class PostExtra(HasImageMixin, models.Model):
    base = models.OneToOneField(Post, related_name='extra')
    slug = models.CharField(max_length=256, blank=True)

    candidates_locked = models.BooleanField(default=False)
    elections = models.ManyToManyField(Election, related_name='posts')
    group = models.CharField(max_length=1024, blank=True)
    party_set = models.ForeignKey('PartySet', blank=True, null=True)

    @property
    def short_label(self):
        from candidates.election_specific import shorten_post_label
        return shorten_post_label(self.base.label)


class MembershipExtra(models.Model):
    base = models.OneToOneField(Membership, related_name='extra')

    elected = models.NullBooleanField()
    party_list_position = models.IntegerField(null=True)
    election = models.ForeignKey(
        Election, blank=True, null=True, related_name='candidacies'
    )

class AreaExtra(models.Model):
    base = models.OneToOneField(Area, related_name='extra')

    type = models.ForeignKey(AreaType, blank=True, null=True, related_name='areas')


class PartySet(models.Model):
    slug = models.CharField(max_length=256)
    name = models.CharField(max_length=1024)
    parties = models.ManyToManyField(Organization, related_name='party_sets')

    def __unicode__(self):
        return self.name

    def party_choices(self):
        result = list(self.parties.order_by('name').values_list('id', 'name'))
        result.insert(0, ('party:none', ''))
        return result
