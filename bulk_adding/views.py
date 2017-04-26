# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import transaction
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.text import slugify

from braces.views import LoginRequiredMixin

from auth_helpers.views import GroupRequiredMixin, user_in_group
from elections.models import Election
from candidates.models import PostExtra, PersonExtra, MembershipExtra
from candidates.models.auth import check_creation_allowed, check_update_allowed
from candidates.views.version_data import get_change_metadata, get_client_ip
from candidates.views.people import get_call_to_action_flash_message
from candidates.models import LoggedAction
from popolo.models import Person, Membership, Organization
from official_documents.models import OfficialDocument
from official_documents.views import get_add_from_document_cta_flash_message
from moderation_queue.models import SuggestedPostLock

from . import forms


class BaseBulkAddView(LoginRequiredMixin, TemplateView):
    # required_group_name = models.TRUSTED_TO_BULK_ADD_GROUP_NAME

    def add_election_and_post_to_context(self, context):
        context['post_extra'] = PostExtra.objects.get(slug=context['post_id'])
        context['election_obj'] = Election.objects.get(slug=context['election'])
        context['parties'] = context['post_extra'].party_set.party_choices(
            exclude_deregistered=True, include_description_ids=True)
        context['official_document'] = OfficialDocument.objects.filter(
            post__extra__slug=context['post_id'],
            election__slug=context['election'],
            ).first()
        self.official_document = context['official_document']
        return context

    def remaining_posts_for_sopn(self):
        return OfficialDocument.objects.filter(
            source_url=self.official_document.source_url,
            post__extra__suggestedpostlock=None
        )

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
            'parties': context['parties'],
        }

        if 'official_document' in context and \
                context['official_document'] is not None:
            form_kwargs['source'] = context['official_document'].source_url,

        if self.request.POST:
            context['formset'] = forms.BulkAddFormSet(
                self.request.POST, **form_kwargs
            )
        else:
            context['formset'] = forms.BulkAddFormSet(
                **form_kwargs
            )

        people_set = set()
        for membership in context['post_extra'].base.memberships.filter(
                extra__election=context['election_obj']):
            person = membership.person
            person.party = membership.on_behalf_of
            people_set.add(person)

        known_people = list(people_set)
        known_people.sort(key=lambda i: i.name.split(' ')[-1])
        context['known_people'] = known_people

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

        initial = []

        for form in self.request.session['bulk_add_data']:
            if form:
                if '__' in form['party']:
                    org_id, other_name_id = form['party'].split('__')
                    org = Organization.objects.get(pk=org_id)
                    desc = org.other_names.get(pk=other_name_id)
                else:
                    desc = Organization.objects.get(pk=form['party']).name

                form['party_description'] = desc
                initial.append(form)

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

        return person_extra

    def update_person(self, context, data, person_extra):
        party = Organization.objects.get(pk=data['party'].split('__')[0])
        post = context['post_extra'].base
        election = Election.objects.get(slug=context['election'])

        previous_memberships_in_this_election = Membership.objects.filter(
            person=person_extra.base,
            extra__election=election,
            role=election.candidate_membership_role,
        )

        previous_memberships_in_this_election.delete()
        person_extra.not_standing.remove(election)

        membership, _ = Membership.objects.get_or_create(
            post=post,
            person=person_extra.base,
            extra__election=election,
            role=election.candidate_membership_role,
            defaults={
                'on_behalf_of': party,
            }
        )

        MembershipExtra.objects.get_or_create(
            base=membership,
            defaults={
                'party_list_position': None,
                'election': election,
                'elected': False,
            }
        )

        change_metadata = get_change_metadata(
            self.request, data['source']
        )

        person_extra.record_version(change_metadata)
        person_extra.save()

        LoggedAction.objects.create(
            user=self.request.user,
            person=person_extra.base,
            action_type='person-update',
            ip_address=get_client_ip(self.request),
            popit_person_new_version=change_metadata['version_id'],
            source=change_metadata['information_source'],
        )

    def form_valid(self, context):

        with transaction.atomic():
            for person_form in context['formset']:
                data = person_form.cleaned_data
                if data.get('select_person') == "_new":
                    # Add a new person
                    person_extra = self.add_person(data)
                else:
                    person_extra = PersonExtra.objects.get(
                        base__pk=int(data['select_person']))
                self.update_person(context, data, person_extra)
            if self.request.POST.get('suggest_locking') == 'on':
                SuggestedPostLock.objects.create(
                    user=self.request.user,
                    post_extra=context['post_extra'],
                )
        if self.remaining_posts_for_sopn().exists():
            messages.add_message(
                self.request,
                messages.SUCCESS,
                get_add_from_document_cta_flash_message(
                    self.official_document,
                    self.remaining_posts_for_sopn()
                ),
                extra_tags='safe do-something-else'
            )

            url = reverse('posts_for_document', kwargs={
                'pk': self.official_document.pk
            })
        else:
            url = reverse('constituency', kwargs={
                'election': context['election'],
                'post_id': context['post_extra'].slug,
                'ignored_slug': slugify(context['post_extra'].base.label),
            })
        return HttpResponseRedirect(url)

    def form_invalid(self, context):
        return self.render_to_response(context)


class UnlockedWithDocumentsView(TemplateView):
    template_name = "official_documents/unlocked_with_documents.html"

    def get_context_data(self, **kwargs):
        context = super(
            UnlockedWithDocumentsView, self).get_context_data(**kwargs)

        SOPNs_qs = OfficialDocument.objects.filter(
            election__current=True).select_related(
                'election', 'post__extra',
                'post__extra__postextraelection'
            )

        SOPNs_qs = SOPNs_qs.exclude(
            post__in=SuggestedPostLock.objects.all().values(
                'post_extra__base'))

        context['unlocked_sopns'] = SOPNs_qs.filter(
            post__extra__postextraelection__candidates_locked=False)

        return context
