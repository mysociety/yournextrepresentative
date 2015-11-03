from datetime import date

from slugify import slugify

from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext as _

from elections.models import Election
from popolo.models import Person, Organization, Post, Membership
from .popit import form_complex_fields_locations, parse_approximate_date

"""Extensions to the base django-popolo classes for YourNextRepresentative

These are done via explicit one-to-one fields to avoid the performance
problems with multi-table inheritance; it's preferable to state when you
want a join or not.

  http://stackoverflow.com/q/23466577/223092

"""


class PersonExtra(models.Model):
    base = models.OneToOneField(Person, related_name='extra')

    # These two fields are added just for Burkina Faso - we should
    # have a better way of adding arbitrary fields which are only
    # needed for one site.
    cv = models.TextField(blank=True)
    program = models.TextField(blank=True)

    # FIXME: have to add multiple images

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

class OrganizationExtra(models.Model):
    base = models.OneToOneField(Organization, related_name='extra')

    # For parties, which party register is it on:
    register = models.CharField(blank=True, max_length=512)
    # FIXME: have to add multiple images (e.g. for party logos)


class PostExtra(models.Model):
    base = models.OneToOneField(Post, related_name='extra')

    elections = models.ManyToManyField(Election, related_name='posts')

    @property
    def short_label(self):
        from candidates.election_specific import AREA_POST_DATA
        return AREA_POST_DATA.shorten_post_label(self.base.label)


class MembershipExtra(models.Model):
    base = models.OneToOneField(Membership, related_name='extra')

    election = models.ForeignKey(
        Election, blank=True, null=True, related_name='candidacies'
    )
