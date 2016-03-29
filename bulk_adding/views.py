# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import transaction
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.text import slugify

from auth_helpers.views import GroupRequiredMixin, user_in_group

from elections.models import Election
from candidates.models import PostExtra, PersonExtra, MembershipExtra
from candidates.models.auth import check_creation_allowed, check_update_allowed
from candidates.views.version_data import get_change_metadata, get_client_ip
from candidates.views.people import get_call_to_action_flash_message
from candidates.models import LoggedAction
from popolo.models import Person, Post, Organization, Membership

from . import forms
from . import models


class BaseBulkAddView(GroupRequiredMixin, TemplateView):
    required_group_name = models.TRUSTED_TO_BULK_ADD_GROUP_NAME

    def add_election_and_post_to_context(self, context):
        context['post_extra'] = PostExtra.objects.get(slug=context['post_id'])
        context['parties'] = context['post_extra'].party_set.parties
        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        if context['formset'].is_valid():
            return self.form_valid(context)
        else:
            return self.form_invalid(context)


class BulkAddView(BaseBulkAddView):
    template_name = "bulk_add/add_form.html"

    def get_context_data(self, **kwargs):
        context = super(BulkAddView, self).get_context_data(**kwargs)
        context.update(self.add_election_and_post_to_context(context))

        form_kwargs = {
            'parties': context['parties']
        }
        if self.request.POST:
            context['formset'] = forms.BulkAddFormSet(
                self.request.POST, **form_kwargs
            )
        else:
            context['formset'] = forms.BulkAddFormSet(
                **form_kwargs
            )


        return context

    def form_valid(self, context):
        self.request.session['bulk_add_data'] = context['formset'].cleaned_data
        return HttpResponseRedirect(
            reverse('bulk_add_review', kwargs={
                'election': context['election'],
                'post_id': context['post_id'],
            })
        )

    def form_invalid(self, context):
        return self.render_to_response(context)


class BulkAddReviewView(BaseBulkAddView):
    template_name = "bulk_add/add_review_form.html"

    def get_context_data(self, **kwargs):
        context = super(BulkAddReviewView, self).get_context_data(**kwargs)
        context.update(self.add_election_and_post_to_context(context))

        initial = [form for form in self.request.session['bulk_add_data'] if form]
        if self.request.POST:
            context['formset'] = forms.BulkAddReviewFormSet(
                self.request.POST, parties=context['parties']
            )
        else:
            context['formset'] = forms.BulkAddReviewFormSet(
                initial=initial, parties=context['parties']
            )

        return context

    def add_person(self, person_data):
        # TODO Move this out of the view layer
        with transaction.atomic():
            person = Person.objects.create(name=person_data['name'])
            person_extra = PersonExtra.objects.create(base=person)
            check_creation_allowed(
                self.request.user, person_extra.current_candidacies
            )

            change_metadata = get_change_metadata(
                self.request, person_data['source']
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
            return person_extra

    def update_person(self, context, data, person_extra):
        party = data['party']
        post = context['post_extra'].base
        election = Election.objects.get(slug=context['election'])

        candidacy_qs = Membership.objects.filter(
            extra__election=election,
            role=election.candidate_membership_role,
            person__extra=person_extra
        )

        membership, _ = Membership.objects.get_or_create(
            post=post,
            on_behalf_of=party,
            person=person_extra.base,
            role=election.candidate_membership_role,
        )

        MembershipExtra.objects.get_or_create(
            base=membership,
            party_list_position=None,
            election=election,
            elected=False,
        )

    def form_valid(self, context):
        for person_form in context['formset']:
            data = person_form.cleaned_data
            if data.get('select_person') == "_new":
                # Add a new person
                person_extra = self.add_person(data)
            else:
                person_extra = PersonExtra.objects.get(
                    base__pk=int(data['select_person']))
            self.update_person(context, data, person_extra)

        url = reverse('constituency', kwargs={
            'election': context['election'],
            'post_id': context['post_extra'].slug,
            'ignored_slug': slugify(context['post_extra'].base.label),
        })
        return HttpResponseRedirect(url)


    def form_invalid(self, context):
        return self.render_to_response(context)

