from __future__ import unicode_literals

import json

from django.db import connection
from django.db.models import Count, F
from django.http import HttpResponse

from django.views.generic import TemplateView

from candidates.models import MembershipExtra
from elections.mixins import ElectionMixin
from elections.models import Election
from popolo.models import Membership, Person

from .models import get_attention_needed_posts


def get_counts(for_json=True):
    election_id_to_candidates = {
        d['extra__election']: d['count']
        for d in Membership.objects \
            .filter(role=F('extra__election__candidate_membership_role')) \
            .values('extra__election') \
            .annotate(count=Count('extra__election'))
    }
    grouped_elections = Election.group_and_order_elections(for_json=for_json)
    for era_data in grouped_elections:
        for date, elections in era_data['dates'].items():
            for role_data in elections:
                for election_data in role_data['elections']:
                    e = election_data['election']
                    total = election_id_to_candidates.get(e.id, 0)
                    election_counts = {
                        'id': e.slug,
                        'html_id': e.slug.replace('.', '-'),
                        'name': e.name,
                        'total': total,
                    }
                    election_data.update(election_counts)
                    del election_data['election']
    return grouped_elections


class ReportsHomeView(TemplateView):
    template_name = "reports.html"

    def get_context_data(self, **kwargs):
        context = super(ReportsHomeView, self).get_context_data(**kwargs)
        context['all_elections'] = get_counts()
        return context

    def get(self, *args, **kwargs):
        if self.request.GET.get('format') == "json":
            return HttpResponse(
                json.dumps(get_counts(for_json=True)),
                content_type="application/json"
            )
        return super(ReportsHomeView, self).get(*args, **kwargs)


class PartyCountsView(ElectionMixin, TemplateView):
    template_name = "party_counts.html"

    def get_context_data(self, **kwargs):
        context = super(PartyCountsView, self).get_context_data(**kwargs)
        cursor = connection.cursor()
        cursor.execute('''
SELECT oe.slug, o.name, count(m.id) AS count
  FROM popolo_organization o
    INNER JOIN candidates_organizationextra oe ON o.id = oe.base_id
    LEFT OUTER JOIN
      (popolo_membership m
        INNER JOIN candidates_membershipextra me ON me.base_id = m.id
        INNER JOIN elections_election ee ON me.election_id = ee.id AND ee.id = %s)
      ON o.id = m.on_behalf_of_id
  WHERE o.classification = 'Party'
  GROUP BY oe.slug, o.name
  ORDER BY count DESC, o.name;
        ''', [self.election_data.id])
        context['party_counts'] = [
            {
                'party_slug': row[0],
                'party_name': row[1],
                'count': row[2],
            }
            for row in cursor.fetchall()
        ]
        return context


class ConstituencyCountsView(ElectionMixin, TemplateView):
    template_name = "constituency_counts.html"

    def get_context_data(self, **kwargs):
        from candidates.election_specific import shorten_post_label
        context = super(ConstituencyCountsView, self).get_context_data(**kwargs)
        cursor = connection.cursor()
        cursor.execute('''
SELECT pe.slug, p.label, count(m.id) as count
  FROM popolo_post p
    INNER JOIN candidates_postextra pe ON pe.base_id = p.id
    INNER JOIN candidates_postextraelection cppee ON cppee.postextra_id = pe.id
    INNER JOIN elections_election ee ON cppee.election_id = ee.id AND ee.id = %s
    LEFT OUTER JOIN
      (popolo_membership m
        INNER JOIN candidates_membershipextra me
        ON me.base_id = m.id)
      ON m.role = ee.candidate_membership_role AND m.post_id = p.id AND
         me.election_id = ee.id
  GROUP BY pe.slug, p.label
  ORDER BY count DESC;
        ''', [self.election_data.id])
        context['post_counts'] = [
            {
                'post_slug': row[0],
                'post_label': row[1],
                'count': row[2],
                'post_short_label': shorten_post_label(row[1]),
            }
            for row in cursor.fetchall()
        ]
        return context


class AttentionNeededView(TemplateView):
    template_name = "attention_needed.html"

    def get_context_data(self, **kwargs):
        context = super(AttentionNeededView, self).get_context_data(**kwargs)
        context['post_counts'] = get_attention_needed_posts()
        return context
