from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import FormView
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404
from django.db import transaction

from braces.views import LoginRequiredMixin

from formtools.wizard.views import SessionWizardView

from auth_helpers.views import user_in_group

from popolo.models import Membership, Organization, Person, Post
from candidates.models import MembershipExtra

from elections.mixins import ElectionMixin

from .helpers import get_redirect_to_post
from .version_data import get_client_ip, get_change_metadata
from .. import forms

from ..models import LoggedAction, TRUSTED_TO_LOCK_GROUP_NAME


def raise_if_locked(request, post):
    # If you're a user who's trusted to toggle the constituency lock,
    # they're allowed to edit candidacy:
    if user_in_group(request.user, TRUSTED_TO_LOCK_GROUP_NAME):
        return
    # Otherwise, if the constituency is locked, raise an exception:
    if post.extra.candidates_locked:
        raise Exception(_("Attempt to edit a candidacy in a locked constituency"))


class CandidacyCreateView(ElectionMixin, LoginRequiredMixin, FormView):

    form_class = forms.CandidacyCreateForm
    template_name = 'candidates/candidacy-create.html'

    def form_valid(self, form):
        post_id = form.cleaned_data['post_id']
        post = get_object_or_404(Post, extra__slug=post_id)
        raise_if_locked(self.request, post)
        change_metadata = get_change_metadata(
            self.request, form.cleaned_data['source']
        )
        with transaction.atomic():
            person = get_object_or_404(Person, id=form.cleaned_data['person_id'])
            LoggedAction.objects.create(
                user=self.request.user,
                action_type='candidacy-create',
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata['version_id'],
                person=person,
                source=change_metadata['information_source'],
            )

            membership_exists = Membership.objects.filter(
                person=person,
                post=post,
                role=self.election_data.candidate_membership_role,
                extra__election=self.election_data
            ).exists()

            if not membership_exists:
                membership = Membership.objects.create(
                    person=person,
                    post=post,
                    role=self.election_data.candidate_membership_role,
                    on_behalf_of=person.extra.last_party(),
                )
                MembershipExtra.objects.create(
                    base=membership,
                    election=self.election_data
                )

            person.extra.not_standing.remove(self.election_data)

            person.extra.record_version(change_metadata)
            person.extra.save()
        return get_redirect_to_post(self.election, post)

    def get_context_data(self, **kwargs):
        context = super(CandidacyCreateView, self).get_context_data(**kwargs)
        context['person'] = get_object_or_404(Person, id=self.request.POST.get('person_id'))
        post = get_object_or_404(Post, extra__slug=self.request.POST.get('post_id'))
        context['post_label'] = post.label
        return context


class CandidacyDeleteView(ElectionMixin, LoginRequiredMixin, FormView):

    form_class = forms.CandidacyDeleteForm
    template_name = 'candidates/candidacy-delete.html'

    def form_valid(self, form):
        post_id = form.cleaned_data['post_id']
        with transaction.atomic():
            post = get_object_or_404(Post, extra__slug=post_id)
            raise_if_locked(self.request, post)
            change_metadata = get_change_metadata(
                self.request, form.cleaned_data['source']
            )
            person = get_object_or_404(Person, id=form.cleaned_data['person_id'])
            LoggedAction.objects.create(
                user=self.request.user,
                action_type='candidacy-delete',
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata['version_id'],
                person=person,
                source=change_metadata['information_source'],
            )

            person.memberships.filter(
                post=post,
                role=self.election_data.candidate_membership_role,
                extra__election=self.election_data,
            ).delete()

            person.extra.not_standing.add(self.election_data)

            person.extra.record_version(change_metadata)
            person.extra.save()
        return get_redirect_to_post(self.election, post)

    def get_context_data(self, **kwargs):
        context = super(CandidacyDeleteView, self).get_context_data(**kwargs)
        context['person'] = get_object_or_404(Person, id=self.request.POST.get('person_id'))
        post = get_object_or_404(Post, extra__slug=self.request.POST.get('post_id'))
        context['post_label'] = post.label
        return context

WIZARD_TEMPLATES = {
    'election': 'candidates/person-edit-candidacy-pick-election.html',
    'post': 'candidates/person-edit-candidacy-pick-post.html',
    'party': 'candidates/person-edit-candidacy-pick-party.html',
    'source': 'candidates/person-edit-candidacy-source.html',
}

WIZARD_FORMS = [
    ('election', forms.AddCandidacyPickElectionForm),
    ('post', forms.AddCandidacyPickPostForm),
    ('party', forms.AddCandidacyPickPartyForm),
    ('source', forms.AddCandidacySourceForm),
]

def do_candidacy_wizard_post_step(wizard):
    election_step_data = wizard.get_cleaned_data_for_step('election')
    if not election_step_data:
        return False
    return election_step_data['election'].number_of_posts != 1


WIZARD_CONDITION_DICT = {
    'post': do_candidacy_wizard_post_step
}

class AddCandidacyWizardView(LoginRequiredMixin, SessionWizardView):

    form_list = WIZARD_FORMS
    condition_dict = WIZARD_CONDITION_DICT

    def dispatch(self, request, *args, **kwargs):
        self.person = get_object_or_404(
            Person.objects.select_related('extra'),
            pk=self.kwargs['person_id'])
        return super(AddCandidacyWizardView, self).dispatch(
            request, *args, **kwargs)

    def get_template_names(self):
        return [WIZARD_TEMPLATES[self.steps.current]]

    def get_post_slug(self):
        cleaned_data_post = self.get_cleaned_data_for_step('post')
        if cleaned_data_post:
            return cleaned_data_post['post']
        # Otherwise, if there's only one post for the election, return
        # that.
        election = self.get_cleaned_data_for_step('election')['election']
        return election.postextraelection_set.get().postextra.slug

    def get_form_kwargs(self, step=None):
        kwargs = super(AddCandidacyWizardView, self).get_form_kwargs(step)
        if step == 'election':
            return kwargs
        elif step == 'post':
            cleaned_data = self.get_cleaned_data_for_step('election')
            kwargs['election'] = cleaned_data['election']
        elif step == 'party':
            cleaned_data_election = self.get_cleaned_data_for_step('election')
            kwargs['election'] = cleaned_data_election['election']
            kwargs['post'] = self.get_post_slug()
        return kwargs

    def get_context_data(self, form, **kwargs):
        context = super(AddCandidacyWizardView, self).get_context_data(form, **kwargs)
        context['person'] = self.person
        return context

    def done(self, form_list, **kwargs):
        form_election, form_post, form_party, form_source = form_list
        election = form_election.cleaned_data['election']
        post_slug = self.get_post_slug()
        post = get_object_or_404(Post, extra__slug=post_slug)
        party_id = form_party.cleaned_data['party']
        party = get_object_or_404(Organization, pk=party_id)
        party_list_position = form_party.cleaned_data.get('party_list_position')
        raise_if_locked(self.request, post)
        change_metadata = get_change_metadata(
            self.request, form_source.cleaned_data['source']
        )
        with transaction.atomic():
            LoggedAction.objects.create(
                user=self.request.user,
                action_type='candidacy-create',
                ip_address=get_client_ip(self.request),
                popit_person_new_version=change_metadata['version_id'],
                person=self.person,
                source=change_metadata['information_source'],
            )

            membership_exists = Membership.objects.filter(
                person=self.person,
                post=post,
                role=election.candidate_membership_role,
                extra__election=election
            ).exists()

            if not membership_exists:
                membership = Membership.objects.create(
                    person=self.person,
                    post=post,
                    role=election.candidate_membership_role,
                    on_behalf_of=party,
                )
                MembershipExtra.objects.create(
                    base=membership,
                    election=election,
                    party_list_position=party_list_position
                )

            self.person.extra.not_standing.remove(election)

            self.person.extra.record_version(change_metadata)
            self.person.extra.save()
        # You get to the wizard from the person edit page, so redirect
        # back to that:
        return HttpResponseRedirect(
            reverse('person-update', kwargs={'person_id': self.person.id})
        )
