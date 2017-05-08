# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re

from django.db.models import Prefetch
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseBadRequest
from django.views.generic import TemplateView
from django.utils.text import slugify
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404

from candidates.models import AreaExtra, MembershipExtra
from candidates.models.auth import get_edits_allowed, is_post_locked

from elections.models import AreaType, Election

from ..forms import NewPersonForm, ToggleLockForm
from .helpers import (
    split_candidacies, group_candidates_by_party,
    get_person_form_fields, split_by_elected
)

class AreasView(TemplateView):
    template_name = 'candidates/areas.html'

    def get(self, request, *args, **kwargs):
        self.types_and_areas = []
        for type_and_area in kwargs['type_and_area_ids'].split(','):
            if '--' not in type_and_area:
                message = _("Malformed type and area: '{0}'")
                return HttpResponseBadRequest(message.format(type_and_area))
            self.types_and_areas.append(type_and_area.split('--', 1))
        response = super(AreasView, self).get(request, *args, **kwargs)
        return response

    def get_context_data(self, **kwargs):
        context = super(AreasView, self).get_context_data(**kwargs)
        all_area_names = set()
        context['posts'] = []
        any_area_found = False
        no_data_areas = []
        posts_seen = set()
        for area_type_code, area_id in self.types_and_areas:
            area_extras = AreaExtra.objects \
                .select_related('base', 'type') \
                .prefetch_related('base__posts') \
                .filter(base__identifier=area_id)
            if area_extras.exists():
                any_area_found = True
            else:
                continue

            for area_extra in area_extras:
                area = area_extra.base
                all_area_names.add(area.name)
                for post in area.posts.all():
                    post_extra = post.extra
                    try:
                        election = post_extra.elections.get(current=True)
                    except Election.DoesNotExist:
                        continue
                    if post.id in posts_seen:
                        continue
                    else:
                        posts_seen.add(post.id)
                    locked = is_post_locked(post, election)
                    extra_qs = MembershipExtra.objects.select_related('election')
                    current_candidacies, _ = split_candidacies(
                        election,
                        post.memberships.prefetch_related(
                            Prefetch('extra', queryset=extra_qs)
                        ).select_related(
                            'person', 'person__extra', 'on_behalf_of',
                            'on_behalf_of__extra', 'organization'
                        ).all()
                    )
                    elected_candidacies, unelected_candidacies = split_by_elected(
                        election,
                        current_candidacies,
                    )
                    elected_candidacies = group_candidates_by_party(
                        election,
                        elected_candidacies,
                    )
                    unelected_candidacies = group_candidates_by_party(
                        election,
                        unelected_candidacies,
                    )
                    post_context = {
                        'election': election.slug,
                        'election_data': election,
                        'post_data': {
                            'id': post.extra.slug,
                            'label': post.label,
                        },
                        'candidates_locked': locked,
                        'lock_form': ToggleLockForm(
                            initial={
                                'post_id': post.extra.slug,
                                'lock': not locked
                            },
                        ),
                        'candidate_list_edits_allowed':
                        get_edits_allowed(self.request.user, locked),
                        'has_elected': \
                            len(elected_candidacies['parties_and_people']) > 0,
                        'elected': elected_candidacies,
                        'unelected': unelected_candidacies,
                        'add_candidate_form': NewPersonForm(
                            election=election.slug,
                            initial={
                                ('constituency_' + election.slug): post_extra.slug,
                                ('standing_' + election.slug): 'standing',
                            },
                            hidden_post_widget=True,
                        ),
                    }

                    post_context = get_person_form_fields(
                        post_context,
                        post_context['add_candidate_form']
                    )

                    context['posts'].append(post_context)

        context['no_data_areas'] = no_data_areas

        if not any_area_found:
            raise Http404("No such areas found")
        context['all_area_names'] = ' — '.join(all_area_names)
        context['suppress_official_documents'] = True
        return context

class AreasOfTypeView(TemplateView):
    template_name = 'candidates/areas-of-type.html'

    def get_context_data(self, **kwargs):
        context = super(AreasOfTypeView, self).get_context_data(**kwargs)
        requested_area_type = kwargs['area_type']
        all_area_tuples = set(
            (area_type.name, election_data.area_generation)
            for election_data in Election.objects.current().by_date()
            for area_type in election_data.area_types.all()
            if area_type.name == requested_area_type
        )
        if not all_area_tuples:
            raise Http404(_("Area '{0}' not found").format(requested_area_type))
        if len(all_area_tuples) > 1:
            message = _("Multiple Area generations for type {area_type} found")
            raise Exception(message.format(area_type=requested_area_type))
        prefetch_qs = AreaExtra.objects.select_related('base').order_by('base__name')
        area_type = get_object_or_404(
            AreaType.objects \
                .prefetch_related(Prefetch('areas', queryset=prefetch_qs)),
            name=requested_area_type
        )
        areas = [
            (
                reverse(
                    'areas-view',
                    kwargs={
                        'type_and_area_ids': '{type}--{area_id}'.format(
                            type=requested_area_type,
                            area_id=area.base.identifier
                        ),
                        'ignored_slug': slugify(area.base.name)
                    }
                ),
                area.base.name,
                requested_area_type,
            )
            for area in area_type.areas.all()
        ]
        context['areas'] = areas
        context['area_type'] = area_type
        return context
