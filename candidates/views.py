from datetime import datetime, timedelta
from random import randint
import re
import sys

from slugify import slugify
import unicodedata

from django.db.models import Count
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.utils import timezone
from django.utils.http import urlquote
from django.views.generic import FormView, TemplateView, View

from braces.views import LoginRequiredMixin, SuperuserRequiredMixin

from .diffs import get_version_diffs
from .forms import (
    PostcodeForm, NewPersonForm, UpdatePersonForm, ConstituencyForm,
    CandidacyCreateForm, CandidacyDeleteForm
)
from .mapit import get_wmc_from_postcode
from .models import (
    PopItPerson,
    get_constituency_name_from_mapit_id,
    all_form_fields,
    get_mapit_id_from_mapit_url,
    membership_covers_date, election_date_2010, election_date_2015,
    LoggedAction, PersonRedirect
)
from .popit import PopItApiMixin, merge_popit_people
from .static_data import MapItData, PartyData

from .update import PersonParseMixin, PersonUpdateMixin

def get_redirect_from_mapit_id(mapit_id):
    constituency_name = get_constituency_name_from_mapit_id(mapit_id)
    return HttpResponseRedirect(
        reverse(
            'constituency',
            kwargs={
                'mapit_area_id': mapit_id,
                'ignored_slug': slugify(constituency_name),
            }
        )
    )

# From http://stackoverflow.com/a/517974/223092
def strip_accents(s):
    return u"".join(
        c for c in unicodedata.normalize('NFKD', s)
        if not unicodedata.combining(c)
    )

def get_electionleaflets_url(constituency_name):
    """Generate an electionleaflets.org URL from a constituency name

    >>> get_electionleaflets_url(u"Ynys M\u00F4n")
    u'http://electionleaflets.org/constituencies/ynys_mon/'
    >>> get_electionleaflets_url(u"Ashton-under-Lyne")
    u'http://electionleaflets.org/constituencies/ashton_under_lyne/'
    >>> get_electionleaflets_url(u"Ayr, Carrick and Cumnock")
    u'http://electionleaflets.org/constituencies/ayr_carrick_and_cumnock/'
    """
    result = strip_accents(constituency_name)
    result = result.lower()
    result = re.sub(r'[^a-z]+', ' ', result)
    result = re.sub(r'\s+', ' ', result).strip()
    slug = result.replace(' ', '_')
    return u'http://electionleaflets.org/constituencies/{}/'.format(slug)


class ContributorsMixin(object):

    def get_leaderboards(self):
        result = []
        for title, since in [
            ('All Time', None),
            ('In the last week', timezone.now() - timedelta(days=7))
        ]:
            if since:
                qs = LoggedAction.objects.filter(created__gt=since)
            else:
                qs = LoggedAction.objects.all()
            rows = qs.values('user'). \
                annotate(edit_count=Count('user')).order_by('-edit_count')[:10]
            for row in rows:
                row['username'] = User.objects.get(pk=row['user'])
            leaderboard = {
                'title': title,
                'rows': rows,
            }
            result.append(leaderboard)
        return result

    def get_recent_changes_queryset(self):
        return LoggedAction.objects.all().order_by('-created')


class ConstituencyPostcodeFinderView(ContributorsMixin, FormView):
    template_name = 'candidates/finder.html'
    form_class = PostcodeForm

    def form_valid(self, form):
        wmc = get_wmc_from_postcode(form.cleaned_data['postcode'])
        return get_redirect_from_mapit_id(wmc)

    def get_context_data(self, **kwargs):
        context = super(ConstituencyPostcodeFinderView, self).get_context_data(**kwargs)
        context['postcode_form'] = kwargs.get('form') or PostcodeForm()
        context['constituency_form'] = ConstituencyForm()
        context['show_postcode_form'] = True
        context['show_name_form'] = False
        context['top_users'] = self.get_leaderboards()[1]['rows'][:8]
        context['recent_actions'] = self.get_recent_changes_queryset()[:5]
        return context


class ConstituencyNameFinderView(ContributorsMixin, FormView):
    template_name = 'candidates/finder.html'
    form_class = ConstituencyForm

    def form_valid(self, form):
        constituency_id = form.cleaned_data['constituency']
        return get_redirect_from_mapit_id(constituency_id)

    def get_context_data(self, **kwargs):
        context = super(ConstituencyNameFinderView, self).get_context_data(**kwargs)
        context['postcode_form'] = PostcodeForm()
        context['constituency_form'] = kwargs.get('form') or ConstituencyForm()
        context['show_postcode_form'] = False
        context['show_name_form'] = True
        context['top_users'] = self.get_leaderboards()[1]['rows'][:8]
        context['recent_actions'] = self.get_recent_changes_queryset()[:5]
        return context


class ConstituencyDetailView(PopItApiMixin, TemplateView):
    template_name = 'candidates/constituency.html'

    def get_context_data(self, **kwargs):
        context = super(ConstituencyDetailView, self).get_context_data(**kwargs)

        context['mapit_area_id'] = mapit_area_id = kwargs['mapit_area_id']
        context['constituency_name'] = \
            get_constituency_name_from_mapit_id(mapit_area_id)

        context['electionleaflets_url'] = \
            get_electionleaflets_url(context['constituency_name'])

        context['redirect_after_login'] = \
            urlquote(reverse('constituency', kwargs={
                'mapit_area_id': mapit_area_id,
                'ignored_slug': slugify(context['constituency_name'])
            }))

        mp_post = self.api.posts(mapit_area_id).get(
            embed='membership.person.membership.organization')

        current_candidates = set()
        past_candidates = set()

        for membership in mp_post['result']['memberships']:
            if not membership['role'] == "Candidate":
                continue
            person = PopItPerson.create_from_dict(membership['person_id'])
            if membership_covers_date(membership, election_date_2010):
                past_candidates.add(person)
            elif membership_covers_date(membership, election_date_2015):
                current_candidates.add(person)
            else:
                raise ValueError("Candidate membership doesn't cover any \
                                  known election date")

        context['candidates_2010_standing_again'] = \
            past_candidates.intersection(current_candidates)

        other_candidates_2010 = past_candidates - current_candidates

        # Now split those candidates into those that we know aren't
        # standing again, and those that we just don't know about:
        context['candidates_2010_not_standing_again'] = \
            set(p for p in other_candidates_2010 if p.not_standing_in_2015)

        context['candidates_2010_might_stand_again'] = \
            set(p for p in other_candidates_2010 if not p.known_status_in_2015)

        context['candidates_2015'] = current_candidates

        context['add_candidate_form'] = NewPersonForm(
            initial={'constituency': mapit_area_id}
        )

        return context


class ConstituencyListView(PopItApiMixin, TemplateView):
    template_name = 'candidates/constituencies.html'

    def get_context_data(self, **kwargs):
        context = super(ConstituencyListView, self).get_context_data(**kwargs)
        context['all_constituencies'] = \
            MapItData.constituencies_2010_name_sorted
        return context


class CandidacyMixin(object):

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[-1].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def create_version_id(self):
        """Generate a random ID to use to identify a person version"""
        return "{0:016x}".format(randint(0, sys.maxint))

    def get_current_timestamp(self):
        return datetime.utcnow().isoformat()

    def get_change_metadata(self, request, information_source):
        result = {
            'information_source': information_source,
            'version_id': self.create_version_id(),
            'timestamp': self.get_current_timestamp()
        }
        if request is not None:
            result['username'] = request.user.username
        return result

    def get_area_from_post_id(self, post_id, mapit_url_key='id'):
        "Get a MapIt area ID from a candidate list organization's PopIt data"

        mapit_data = MapItData.constituencies_2010.get(post_id)
        if mapit_data is None:
            message = "Couldn't find the constituency with Post and MapIt Area ID: '{0}'"
            raise Exception(message.format(post_id))
        url_format = 'http://mapit.mysociety.org/area/{0}'
        return {
            'name': mapit_data['name'],
            'post_id': post_id,
            mapit_url_key: url_format.format(post_id),
        }


class CandidacyView(LoginRequiredMixin, CandidacyMixin, PersonParseMixin, PersonUpdateMixin, FormView):

    form_class = CandidacyCreateForm
    template_name = 'candidates/candidacy-create.html'

    def form_valid(self, form):
        change_metadata = self.get_change_metadata(
            self.request, form.cleaned_data['source']
        )
        LoggedAction.objects.create(
            user=self.request.user,
            action_type='candidacy-create',
            ip_address=self.get_client_ip(self.request),
            popit_person_new_version=change_metadata['version_id'],
            popit_person_id=form.cleaned_data['person_id'],
            source=change_metadata['information_source'],
        )
        our_person = self.get_person(form.cleaned_data['person_id'])
        previous_versions = our_person.pop('versions')

        our_person['standing_in']['2015'] = self.get_area_from_post_id(
            form.cleaned_data['mapit_area_id'],
            mapit_url_key='mapit_url'
        )
        our_person['party_memberships']['2015'] = our_person['party_memberships']['2010']

        self.update_person(our_person, change_metadata, previous_versions)
        return get_redirect_from_mapit_id(form.cleaned_data['mapit_area_id'])

    def get_context_data(self, **kwargs):
        context = super(CandidacyView, self).get_context_data(**kwargs)
        context['person'] = self.get_person(self.request.POST.get('person_id'))
        context['constituency'] = MapItData.constituencies_2010.get(
            self.request.POST.get('mapit_area_id')
        )
        return context


class CandidacyDeleteView(LoginRequiredMixin, CandidacyMixin, PersonParseMixin, PersonUpdateMixin, FormView):

    form_class = CandidacyDeleteForm
    template_name = 'candidates/candidacy-delete.html'

    def form_valid(self, form):
        change_metadata = self.get_change_metadata(
            self.request, form.cleaned_data['source']
        )
        LoggedAction.objects.create(
            user=self.request.user,
            action_type='candidacy-delete',
            ip_address=self.get_client_ip(self.request),
            popit_person_new_version=change_metadata['version_id'],
            popit_person_id=form.cleaned_data['person_id'],
            source=change_metadata['information_source'],
        )
        our_person = self.get_person(form.cleaned_data['person_id'])
        previous_versions = our_person.pop('versions')

        our_person['standing_in']['2015'] = None
        our_person['party_memberships'].pop('2015', None)

        self.update_person(our_person, change_metadata, previous_versions)
        return get_redirect_from_mapit_id(form.cleaned_data['mapit_area_id'])

    def get_context_data(self, **kwargs):
        context = super(CandidacyDeleteView, self).get_context_data(**kwargs)
        context['person'] = self.get_person(self.request.POST.get('person_id'))
        context['constituency'] = MapItData.constituencies_2010.get(
            self.request.POST.get('mapit_area_id')
        )
        return context

def get_previous_constituency_name(standing_in):
    for year in reversed(standing_in.keys()):
        if standing_in[year]:
            return standing_in[year]['name']
    return None

def copy_person_form_data(cleaned_data):
    result = cleaned_data.copy()
    # The date is returned as a datetime.date, so if that's set, turn
    # it into a string:
    birth_date_date = result['birth_date']
    if birth_date_date:
        result['birth_date'] = str(birth_date_date)
    area_id = result.get('constituency')
    if area_id:
        country_name =  MapItData.constituencies_2010.get(area_id)['country_name']
        key = 'party_ni' if country_name == 'Northern Ireland' else 'party_gb'
        result['party'] = result[key]
    else:
        result['party'] = None
    del result['party_gb']
    del result['party_ni']
    return result


class PersonView(PersonParseMixin, TemplateView):
    template_name = 'candidates/person-view.html'

    def get_last_constituency(self, person_data):
        result = None
        for year in ('2010', '2015'):
            cons = person_data['standing_in'].get(year)
            if cons:
                result = (year, cons)
        return result

    def get_context_data(self, **kwargs):
        context = super(PersonView, self).get_context_data(**kwargs)
        person_data = self.get_person(self.kwargs['person_id'])
        context['person'] = person_data
        context['popit_api_url'] = self.get_base_url()
        context['last_cons'] = self.get_last_constituency(person_data)
        context['redirect_after_login'] = urlquote(
            reverse('person-view', kwargs={'person_id': person_data['id']})
        )
        context['versions'] = get_version_diffs(person_data['versions'])
        return context

    def get(self, request, *args, **kwargs):
        # If there's a PersonRedirect for this person ID, do the
        # redirect, otherwise process the GET request as usual.
        try:
            new_person_id = PersonRedirect.objects.get(
                old_person_id=self.kwargs['person_id']
            ).new_person_id
            # Get the person data so that we can redirect with a
            # useful slug:
            person_data = self.get_person(new_person_id)
            return HttpResponsePermanentRedirect(
                reverse('person-view', kwargs={
                    'person_id': new_person_id,
                    'ignored_slug': slugify(person_data['name']),
                })
            )
        except PersonRedirect.DoesNotExist:
            return super(PersonView, self).get(request, *args, **kwargs)


class RevertPersonView(LoginRequiredMixin, CandidacyMixin, PersonParseMixin, PersonUpdateMixin, View):

    http_method_names = [u'post']

    def post(self, request, *args, **kwargs):
        version_id = self.request.POST['version_id']
        person_id = self.kwargs['person_id']
        source = self.request.POST['source']

        our_person = self.get_person(self.kwargs['person_id'])
        previous_versions = our_person.pop('versions')

        data_to_revert_to = None
        for version in previous_versions:
            if version['version_id'] == version_id:
                data_to_revert_to = version['data']

        if not data_to_revert_to:
            message = "Couldn't find the version {0} of person {1}"
            raise Exception(message.format(version_id, person_id))

        change_metadata = self.get_change_metadata(self.request, source)
        self.update_person(data_to_revert_to, change_metadata, previous_versions)

        return HttpResponseRedirect(
            reverse(
                'person-update',
                kwargs={'person_id': person_id}
            )
        )

class MergePeopleView(SuperuserRequiredMixin, CandidacyMixin, PersonParseMixin, PersonUpdateMixin, View):

    http_method_names = [u'post']

    def post(self, request, *args, **kwargs):
        # Check that the person IDs are well-formed:
        primary_person_id = self.kwargs['person_id']
        secondary_person_id = self.request.POST['other']
        if not re.search('^\d+$', secondary_person_id):
            message = "Malformed person ID '{0}'"
            raise ValueError(message.format(secondary_person_id))
        if primary_person_id == secondary_person_id:
            message = "You can't merge a person ({0}) with themself ({1})"
            raise ValueError(message.format(
                primary_person_id, secondary_person_id
            ))
        # Get our JSON representation of each person:
        primary_person = self.get_person(primary_person_id)
        secondary_person = self.get_person(secondary_person_id)
        # Merge them (which will include a merged versions array):
        merged_person = merge_popit_people(primary_person, secondary_person)
        # Update the primary person in PopIt:
        previous_versions = merged_person.pop('versions')
        change_metadata = self.get_change_metadata(
            self.request, 'After merging person {0}'.format(secondary_person_id)
        )
        self.update_person(merged_person, change_metadata, previous_versions)
        # Now we delete the old person:
        self.api.persons(secondary_person_id).delete()
        # Create a redirect from the old person to the new person:
        PersonRedirect.objects.create(
            old_person_id=secondary_person_id,
            new_person_id=primary_person_id,
        )
        # Log that that action has taken place, and will be shown in
        # the recent changes, leaderboards, etc.
        LoggedAction.objects.create(
            user=self.request.user,
            action_type='person-merge',
            ip_address=self.get_client_ip(self.request),
            popit_person_new_version=change_metadata['version_id'],
            popit_person_id=primary_person_id,
            source=change_metadata['information_source'],
        )
        # And redirect to the primary person with the merged data:
        return HttpResponseRedirect(
            reverse('person-view', kwargs={
                'person_id': primary_person_id,
                'ignored_slug': slugify(primary_person['name']),
            })
        )

class UpdatePersonView(LoginRequiredMixin, CandidacyMixin, PersonParseMixin, PersonUpdateMixin, FormView):
    template_name = 'candidates/person-edit.html'
    form_class = UpdatePersonForm

    def get_initial(self):
        initial_data = super(UpdatePersonView, self).get_initial()
        our_person = self.get_person(self.kwargs['person_id'])
        for field_name in all_form_fields:
            initial_data[field_name] = our_person.get(field_name)
        # FIXME: this whole method could really do with some
        # refactoring, it's way too long and involved:
        standing_in = our_person['standing_in']
        # If there's data from 2010, set that in initial data to
        # provide useful defaults ...
        if '2010' in standing_in:
            area_id_2010 = standing_in['2010']['post_id']
            initial_data['constituency'] = area_id_2010
            country_name =  MapItData.constituencies_2010.get(area_id_2010)['country_name']
            key = 'party_ni' if country_name == 'Northern Ireland' else 'party_gb'
            initial_data[key] = our_person['party_memberships']['2010']['id']
        # ... but if there's data for 2015, it'll overwrite any
        # defaults from 2010:
        if '2015' in standing_in:
            standing_in_2015 = standing_in.get('2015')
            if standing_in_2015 is None:
                initial_data['standing'] = 'not-standing'
            elif standing_in_2015:
                initial_data['standing'] = 'standing'
                # First make sure the constituency select box has the right value:
                cons_data_2015 = our_person['standing_in'].get('2015', {})
                mapit_url = cons_data_2015.get('mapit_url')
                if mapit_url:
                    area_id = get_mapit_id_from_mapit_url(mapit_url)
                    initial_data['constituency'] = area_id
                    # Get the 2015 party ID:
                    party_data_2015 = our_person['party_memberships'].get('2015', {})
                    party_id = party_data_2015.get('id', '')
                    # Get the right country based on that constituency:
                    country = MapItData.constituencies_2010.get(area_id)['country_name']
                    if country == 'Northern Ireland':
                        initial_data['party_ni'] = party_id
                    else:
                        initial_data['party_gb'] = party_id
            else:
                message = "Unexpected 'standing_in' value {0}"
                raise Exception(message.format(standing_in_2015))
        else:
            initial_data['standing'] = 'not-sure'
            # TODO: If we don't know someone to be standing, assume they are
            # still in the same party as they were in 2010
        return initial_data

    def get_context_data(self, **kwargs):
        context = super(UpdatePersonView, self).get_context_data(**kwargs)

        context['person'] = self.api.persons(
            self.kwargs['person_id']
        ).get()['result']

        context['versions'] = get_version_diffs(context['person']['versions'])

        return context

    def form_valid(self, form):
        # First parse that person's data from PopIt into our more
        # usable data structure:

        our_person = self.get_person(self.kwargs['person_id'])
        previous_versions = our_person.pop('versions')

        # Now we need to make any changes to that data structure based
        # on information given in the form.

        data_for_update = copy_person_form_data(form.cleaned_data)

        # Extract some fields that we will deal with separately:
        change_metadata = self.get_change_metadata(
            self.request, data_for_update.pop('source')
        )
        standing = data_for_update.pop('standing')
        constituency_2015_mapit_id = data_for_update.pop('constituency')
        party_2015 = data_for_update.pop('party')

        # Update our representation with data from the form:
        our_person.update(data_for_update)

        LoggedAction.objects.create(
            user=self.request.user,
            action_type='person-update',
            ip_address=self.get_client_ip(self.request),
            popit_person_new_version=change_metadata['version_id'],
            popit_person_id=our_person['id'],
            source=change_metadata['information_source'],
        )

        if standing == 'standing':
            constituency_name = get_constituency_name_from_mapit_id(
                constituency_2015_mapit_id
            )
            if not constituency_name:
                message = "Failed to find a constituency with MapIt ID {}"
                raise Exception(message.format(constituency_2015_mapit_id))
            our_person['standing_in']['2015'] = \
                self.get_area_from_post_id(constituency_2015_mapit_id, mapit_url_key='mapit_url')
            our_person['party_memberships']['2015'] = {
                'name': PartyData.party_id_to_name[party_2015],
                'id': party_2015,
            }
        elif standing == 'not-standing':
            # If the person is not standing in 2015, record that
            # they're not and remove the party membership for 2015:
            our_person['standing_in']['2015'] = None
            if '2015' in our_person['party_memberships']:
                del our_person['party_memberships']['2015']
        elif standing == 'not-sure':
            # If the update specifies that we're not sure if they're
            # standing in 2015, then remove the standing_in and
            # party_memberships entries for that year:
            our_person['standing_in'].pop('2015', None)
            our_person['party_memberships'].pop('2015', None)

        self.update_person(our_person, change_metadata, previous_versions)

        return HttpResponseRedirect(reverse('person-view', kwargs={'person_id': our_person['id']}))


class NewPersonView(LoginRequiredMixin, CandidacyMixin, PersonUpdateMixin, FormView):
    template_name = 'candidates/person-create.html'
    form_class = NewPersonForm

    def form_valid(self, form):
        data_for_creation = copy_person_form_data(form.cleaned_data)

        change_metadata = self.get_change_metadata(
            self.request, data_for_creation.pop('source')
        )
        action = LoggedAction.objects.create(
            user=self.request.user,
            action_type='person-create',
            ip_address=self.get_client_ip(self.request),
            popit_person_new_version=change_metadata['version_id'],
            source=change_metadata['information_source'],
        )
        # Extract these fields, since we'll present them in the
        # standing_in and party_memberships fields.
        party = data_for_creation.pop('party')
        mapit_area_id = data_for_creation.pop('constituency')

        data_for_creation['party_memberships'] = {
            '2015': {
                'name': PartyData.party_id_to_name[party],
                'id': party,
            }
        }

        data_for_creation['standing_in'] = {
            '2015': self.get_area_from_post_id(mapit_area_id,
                                               mapit_url_key='mapit_url')
        }

        person_id = self.create_person(data_for_creation, change_metadata)
        action.popit_person_id = person_id
        action.save()
        return HttpResponseRedirect(reverse('person-view', kwargs={'person_id': person_id}))

class HelpApiView(PopItApiMixin, TemplateView):
    template_name = 'candidates/api.html'

    def get_context_data(self, **kwargs):
        context = super(HelpApiView, self).get_context_data(**kwargs)
        context['popit_url'] = self.get_base_url()
        return context

class HelpAboutView(TemplateView):
    template_name = 'candidates/about.html'

class RecentChangesView(ContributorsMixin, TemplateView):
    template_name = 'candidates/recent-changes.html'

    def get_context_data(self, **kwargs):
        context = super(RecentChangesView, self).get_context_data(**kwargs)
        actions = self.get_recent_changes_queryset()
        paginator = Paginator(actions, 50)
        page = self.request.GET.get('page')
        try:
            context['actions'] = paginator.page(page)
        except PageNotAnInteger:
            context['actions'] = paginator.page(1)
        except EmptyPage:
            context['actions'] = paginator.page(paginator.num_pages)
        return context

class LeaderboardView(ContributorsMixin, TemplateView):
    template_name = 'candidates/leaderboard.html'

    def get_context_data(self, **kwargs):
        context = super(LeaderboardView, self).get_context_data(**kwargs)
        context['leaderboards'] = self.get_leaderboards()
        return context
