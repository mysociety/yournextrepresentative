import json
import re

from slugify import slugify

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import transaction
from django.http import (
    HttpResponseRedirect, HttpResponsePermanentRedirect, Http404,
    HttpResponse
)
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.utils.http import urlquote
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.generic import FormView, TemplateView, View

from braces.views import LoginRequiredMixin

from auth_helpers.views import GroupRequiredMixin, user_in_group
from elections.models import Election
from elections.mixins import ElectionMixin

from ..diffs import get_version_diffs
from .version_data import get_client_ip, get_change_metadata
from ..forms import NewPersonForm, UpdatePersonForm
from ..models import (
    LoggedAction, PersonRedirect,
    TRUSTED_TO_MERGE_GROUP_NAME,
    TRUSTED_TO_LOCK_GROUP_NAME,
)
from ..models.versions import (
    revert_person_from_version_data, get_person_as_version_data
)
from ..models import PersonExtra
from ..popit import merge_popit_people
from popolo.models import Person, Post

def get_call_to_action_flash_message(person, new_person=False):
    """Get HTML for a flash message after a person has been created or updated"""

    return render_to_string(
        'candidates/_person_update_call_to_action.html',
        {
            'new_person': new_person,
            'person_url':
            reverse('person-view', kwargs={'person_id': person.id}),
            'person_edit_url':
            reverse('person-update', kwargs={'person_id': person.id}),
            'person_name': person.name,
            'needing_attention_url': reverse('attention_needed'),
            # We want to offer the option to add another candidate in
            # any of the elections that this candidate is standing in,
            # which means we'll need the "create person" URL and
            # election name for each of those elections:
            'create_for_election_options': [
                (
                    reverse('person-create', kwargs={'election': election_data.slug}),
                    election_data.name
                )
                for election_data in Election.objects.filter(
                        candidacies__base__person=person
                )
            ]
        }
    )


class PersonView(TemplateView):
    template_name = 'candidates/person-view.html'

    @method_decorator(cache_control(max_age=(60 * 20)))
    def dispatch(self, *args, **kwargs):
        return super(PersonView, self).dispatch(
            *args, **kwargs
        )

    def get_context_data(self, **kwargs):
        context = super(PersonView, self).get_context_data(**kwargs)
        path = self.person.extra.get_absolute_url()
        context['redirect_after_login'] = urlquote(path)
        context['canonical_url'] = self.request.build_absolute_uri(path)
        context['person'] = self.person
        context['elections_by_date'] = Election.objects.by_date()
        context['last_candidacy'] = self.person.extra.last_candidacy
        return context

    def get(self, request, *args, **kwargs):
        person_id = self.kwargs['person_id']
        try:
            self.person = Person.objects.select_related('extra'). \
                get(pk=person_id)
        except Person.DoesNotExist:
            raise Http404(_("No person found with ID {person_id}").format(
                person_id=person_id
            ))
        # If there's a PersonRedirect for this person ID, do the
        # redirect, otherwise process the GET request as usual.
        try:
            new_person_id = PersonRedirect.objects.get(
                old_person_id=self.person.id
            ).new_person_id
            return HttpResponsePermanentRedirect(
                reverse('person-view', kwargs={
                    'person_id': new_person_id,
                    'ignored_slug': self.person.extra.get_slug(),
                })
            )
        except PersonRedirect.DoesNotExist:
            return super(PersonView, self).get(request, *args, **kwargs)


class RevertPersonView(LoginRequiredMixin, View):

    http_method_names = [u'post']

    def post(self, request, *args, **kwargs):
        version_id = self.request.POST['version_id']
        person_id = self.kwargs['person_id']
        source = self.request.POST['source']

        person_extra = get_object_or_404(
            PersonExtra.objects.select_related('base'),
            base__id=person_id
        )
        person = person_extra.base

        versions = json.loads(person_extra.versions)

        data_to_revert_to = None
        for version in versions:
            if version['version_id'] == version_id:
                data_to_revert_to = version['data']
                break

        if not data_to_revert_to:
            message = _("Couldn't find the version {0} of person {1}")
            raise Exception(message.format(version_id, person_id))

        with transaction.atomic():

            change_metadata = get_change_metadata(self.request, source)

            # Update the person here...
            revert_person_from_version_data(person, person_extra, data_to_revert_to)

            person_extra.record_version(change_metadata)
            person_extra.save()

            # Log that that action has taken place, and will be shown in
            # the recent changes, leaderboards, etc.
            LoggedAction.objects.create(
                user=self.request.user,
                person=person,
                action_type='person-revert',
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata['version_id'],
                source=change_metadata['information_source'],
            )

        return HttpResponseRedirect(
            reverse(
                'person-view',
                kwargs={'person_id': person_id}
            )
        )

class MergePeopleView(GroupRequiredMixin, View):

    http_method_names = [u'post']
    required_group_name = TRUSTED_TO_MERGE_GROUP_NAME

    def post(self, request, *args, **kwargs):
        # Check that the person IDs are well-formed:
        primary_person_id = self.kwargs['person_id']
        secondary_person_id = self.request.POST['other']
        if not re.search('^\d+$', secondary_person_id):
            message = _("Malformed person ID '{0}'")
            raise ValueError(message.format(secondary_person_id))
        if primary_person_id == secondary_person_id:
            message = _("You can't merge a person ({0}) with themself ({1})")
            raise ValueError(message.format(
                primary_person_id, secondary_person_id
            ))
        primary_person_extra, secondary_person_extra = [
            get_object_or_404(
                PersonExtra.objects.select_related('base'),
                base__id=person_id
            )
            for person_id in (primary_person_id, secondary_person_id)
        ]
        primary_person = primary_person_extra.base
        secondary_person = secondary_person_extra.base
        # Merge the reduced JSON representations:
        merged_person_version_data = merge_popit_people(
            get_person_as_version_data(primary_person),
            get_person_as_version_data(secondary_person),
        )
        # Update the primary person in PopIt:
        change_metadata = get_change_metadata(
            self.request, _('After merging person {0}').format(secondary_person_id)
        )
        revert_person_from_version_data(
            primary_person,
            primary_person_extra,
            merged_person_version_data
        )
        # Make sure the secondary person's version history is appended, so it
        # isn't lost.
        primary_person_versions = json.loads(primary_person_extra.versions)
        primary_person_versions += json.loads(secondary_person_extra.versions)
        primary_person_extra.versions = json.dumps(primary_person_versions)
        primary_person_extra.record_version(change_metadata)
        primary_person_extra.save()
        # Now we delete the old person:
        secondary_person.delete()
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
            ip_address=get_client_ip(self.request),
            popit_person_new_version=change_metadata['version_id'],
            person=primary_person,
            source=change_metadata['information_source'],
        )
        # And redirect to the primary person with the merged data:
        return HttpResponseRedirect(
            reverse('person-view', kwargs={
                'person_id': primary_person_id,
                'ignored_slug': slugify(primary_person.name),
            })
        )

class UpdatePersonView(LoginRequiredMixin, FormView):
    template_name = 'candidates/person-edit.html'
    form_class = UpdatePersonForm

    def get_initial(self):
        initial_data = super(UpdatePersonView, self).get_initial()
        person = get_object_or_404(
            Person.objects.select_related('extra'),
            pk=self.kwargs['person_id']
        )
        initial_data.update(person.extra.get_initial_form_data())
        return initial_data

    def get_context_data(self, **kwargs):
        from ..election_specific import PARTY_DATA
        context = super(UpdatePersonView, self).get_context_data(**kwargs)

        person = get_object_or_404(
            Person.objects.select_related('extra'),
            pk=self.kwargs['person_id']
        )
        context['person'] = person

        context['user_can_merge'] = user_in_group(
            self.request.user,
            TRUSTED_TO_MERGE_GROUP_NAME
        )

        context['versions'] = get_version_diffs(
            json.loads(person.extra.versions)
        )

        context['constituencies_form_fields'] = []
        for election_data in Election.objects.by_date():
            if not election_data.current:
                continue
            cons_form_fields = {
                'election_name': election_data.name,
                'standing': kwargs['form']['standing_' + election_data.slug],
                'constituency': kwargs['form']['constituency_' + election_data.slug],
            }
            party_fields = []
            for ps in PARTY_DATA.ALL_PARTY_SETS:
                key_suffix = ps['slug'] + '_' + election_data.slug
                position_field = None
                if election_data.party_lists_in_use:
                    position_field = kwargs['form']['party_list_position_' + key_suffix]
                party_position_tuple = (
                    kwargs['form']['party_' + key_suffix],
                    position_field
                )
                party_fields.append(party_position_tuple)
            cons_form_fields['party_fields'] = party_fields
            context['constituencies_form_fields'].append(cons_form_fields)

        return context

    def form_valid(self, form):

        if not (settings.EDITS_ALLOWED or self.request.user.is_staff):
            return HttpResponseRedirect(reverse('all-edits-disallowed'))

        # FIXME: not at all sure this is the right thing to do
        for election_data in form.elections_with_fields:
            form_data = form.cleaned_data.copy()
            post_id = form_data.get('constituency_' + election_data.slug)
            post = get_object_or_404(Post, extra__slug=post_id)
            if post.extra.candidates_locked and \
                not user_in_group(self.request.user, TRUSTED_TO_LOCK_GROUP_NAME):
                resp = HttpResponse()
                resp.status_code = 403
                return resp

        with transaction.atomic():

            # FIXME: need to check that if we are changing the post then it's
            # not a locked post
            person = get_object_or_404(
                Person.objects.select_related('extra'),
                id=self.kwargs['person_id']
            )
            person_extra = person.extra
            person_extra.update_from_form(form)
            change_metadata = get_change_metadata(
                self.request, form.cleaned_data.pop('source')
            )
            person_extra.record_version(change_metadata)
            person_extra.save()
            LoggedAction.objects.create(
                user=self.request.user,
                person=person,
                action_type='person-update',
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata['version_id'],
                source=change_metadata['information_source'],
            )

            # Add a message to be displayed after redirect:
            messages.add_message(
                self.request,
                messages.SUCCESS,
                get_call_to_action_flash_message(person, new_person=False),
                extra_tags='safe do-something-else'
            )

        return HttpResponseRedirect(reverse('person-view', kwargs={'person_id': person.id}))


class NewPersonView(ElectionMixin, LoginRequiredMixin, FormView):
    template_name = 'candidates/person-create.html'
    form_class = NewPersonForm

    def get_form_kwargs(self):
        kwargs = super(NewPersonView, self).get_form_kwargs()
        kwargs['election'] = self.election
        return kwargs

    def get_initial(self):
        result = super(NewPersonView, self).get_initial()
        result['standing_' + self.election] = 'standing'
        return result

    def form_valid(self, form):

        if not (settings.EDITS_ALLOWED or self.request.user.is_staff):
            return HttpResponseRedirect(reverse('all-edits-disallowed'))

        # FIXME: not at all sure this is the right thing to do
        for election_data in form.elections_with_fields:
            form_data = form.cleaned_data.copy()
            post_id = form_data.get('constituency_' + election_data.slug)
            post = get_object_or_404(Post, extra__slug=post_id)
            if post.extra.candidates_locked and \
                not user_in_group(self.request.user, TRUSTED_TO_LOCK_GROUP_NAME):
                resp = HttpResponse()
                resp.status_code = 403
                return resp

        with transaction.atomic():

            person_extra = PersonExtra.create_from_form(form)
            person = person_extra.base
            change_metadata = get_change_metadata(
                self.request, form.cleaned_data['source']
            )
            person_extra.record_version(change_metadata)
            person_extra.save()
            LoggedAction.objects.create(
                user=self.request.user,
                person=person,
                action_type='person-create',
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata['version_id'],
                source=change_metadata['information_source'],
            )

            # Add a message to be displayed after redirect:
            messages.add_message(
                self.request,
                messages.SUCCESS,
                get_call_to_action_flash_message(person, new_person=True),
                extra_tags='safe do-something-else'
            )

        return HttpResponseRedirect(reverse('person-view', kwargs={'person_id': person.id}))
