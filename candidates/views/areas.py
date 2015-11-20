# -*- coding: utf-8 -*-

import re

from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseBadRequest
from django.views.generic import TemplateView
from django.utils.text import slugify
from django.utils.translation import ugettext as _
from django.shortcuts import get_object_or_404

from popolo.models import Post

from candidates.cache import UnknownPostException
from candidates.models.auth import get_edits_allowed

from elections.models import Election

from ..forms import NewPersonForm
from .helpers import get_people_from_memberships, group_people_by_party

class AreasView(TemplateView):
    template_name = 'candidates/areas.html'

    def get(self, request, *args, **kwargs):
        self.types_and_areas = []
        for type_and_area in kwargs['type_and_area_ids'].split(','):
            m = re.search(r'^([A-Z0-9]+)-(\d+)$', type_and_area)
            if not m:
                message = _("Malformed type and area: '{0}'")
                return HttpResponseBadRequest(message.format(type_and_area))
            self.types_and_areas.append(m.groups())
        try:
            view = super(AreasView, self).get(request, *args, **kwargs)
        except UnknownPostException:
            message = _("Unknown post for types and areas: '{0}'")
            return HttpResponseBadRequest(message.format(kwargs['type_and_area_ids']))
        return view

    def get_context_data(self, **kwargs):
        from ..election_specific import AREA_POST_DATA, AREA_DATA
        context = super(AreasView, self).get_context_data(**kwargs)
        all_area_names = set()
        context['posts'] = []
        for area_type, area_id in self.types_and_areas:
            # Show candidates from the current elections:
            for election_data in Election.objects.current().by_date():
                area_generation = election_data.area_generation
                if area_type in [area.name for area in election_data.area_types.all()]:
                    area_tuple = (area_type, area_generation)
                    post_id = AREA_POST_DATA.get_post_id(election_data.slug, area_type, area_id)
                    post_data = get_object_or_404(Post, extra__slug=post_id)
                    area_name = AREA_DATA.areas_by_id[area_tuple][area_id]['name']
                    all_area_names.add(area_name)
                    locked = post_data.extra.candidates_locked
                    current_candidates, _ = get_people_from_memberships(
                        election_data,
                        post_data.memberships.all()
                    )

                    current_candidates = group_people_by_party(
                        election_data.slug,
                        current_candidates,
                        party_list=election_data.party_lists_in_use,
                        max_people=election_data.default_party_list_members_to_show
                    )
                    context['posts'].append({
                        'election': election_data.slug,
                        'election_data': election_data,
                        'post_data': post_data,
                        'candidates_locked': locked,
                        'candidate_list_edits_allowed':
                        get_edits_allowed(self.request.user, locked),
                        'candidates': current_candidates,
                        'add_candidate_form': NewPersonForm(
                            election=election_data.slug,
                            initial={
                                ('constituency_' + election_data.slug): post_id,
                                ('standing_' + election_data.slug): 'standing',
                            },
                            hidden_post_widget=True,
                        ),
                    })
        context['all_area_names'] = u' — '.join(all_area_names)
        context['suppress_official_documents'] = True
        return context

class AreasOfTypeView(TemplateView):
    template_name = 'candidates/areas-of-type.html'

    def get_context_data(self, **kwargs):
        from ..election_specific import AREA_DATA
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
        area_tuple = list(all_area_tuples)[0]
        areas = [
            (
                reverse(
                    'areas-view',
                    kwargs={
                        'type_and_area_ids': '{type}-{area_id}'.format(
                            type=requested_area_type,
                            area_id=area['id']
                        ),
                        'ignored_slug': slugify(area['name'])
                    }
                ),
                area['name'],
                area['type_name'],
            )
            for area in AREA_DATA.areas_by_id[area_tuple].values()
        ]
        areas.sort(key=lambda a: a[1])
        context['areas'] = areas
        context['area_type_name'] = _('[No areas found]')
        if areas:
            context['area_type_name'] = areas[0][2]
        return context
