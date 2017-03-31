# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from collections import OrderedDict

from django import forms
from django.db import transaction

from popolo.models import Organization
from candidates.views.version_data import get_change_metadata, get_client_ip
from candidates.models import LoggedAction

from results.models import ResultEvent

from .models import CouncilElectionResultSet, ResultSet
from .constants import CONFIRMED_STATUS


class ReportCouncilElectionControlForm(forms.ModelForm):
    class Meta:
        model = CouncilElectionResultSet
        fields = [
            'council_election',
            'controller',
            'noc',
            'source',
        ]
        widgets = {
            'council_election': forms.HiddenInput(),
            'source': forms.Textarea(
                attrs={'rows': 1, 'columns': 72}
            )
        }

    def __init__(self, council_election, *args, **kwargs):
        super(ReportCouncilElectionControlForm, self).__init__(*args, **kwargs)
        self.fields['controller'].choices = council_election.party_set.party_choices()
        self.fields['controller'].label = "Controlling party"
        self.fields['noc'].label = "No overall control"
        self.fields['council_election'].initial = council_election.pk


    controller = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={
            'class': 'party-select',
        }),
        required=False
    )

    def clean(self, **kwargs):
        if not any(
                (self.cleaned_data['controller'], self.cleaned_data['noc'])):
            raise forms.ValidationError(
                'Please select a party or check "No overall control"')
        if self.cleaned_data.get('controller'):
            self.cleaned_data['controller'] = \
                Organization.objects.get(pk=self.cleaned_data['controller'])
        return self.cleaned_data


class ReviewControlForm(forms.ModelForm):
    class Meta:
        model = CouncilElectionResultSet
        fields = [
            'review_status',
            'reviewed_by',
            'review_source',
        ]
        widgets = {
            'reviewed_by': forms.HiddenInput(),
            'review_source': forms.Textarea(
                attrs={'rows': 1, 'columns': 72}
            )
        }


class ReviewVotesForm(forms.ModelForm):
    class Meta:
        model = ResultSet
        fields = [
            'review_status',
            'reviewed_by',
            'review_source',
        ]
        widgets = {
            'reviewed_by': forms.HiddenInput(),
            'review_source': forms.Textarea(
                attrs={'rows': 1, 'columns': 72}
            )
        }

    def __init__(self, request, review_result, *args, **kwargs):
        self.request = request
        self.post = review_result.post_result.post

        super(ReviewVotesForm, self).__init__(*args, **kwargs)

    def mark_candidates_as_winner(self, request, instance):
        for candidate_result in instance.candidate_results.all():
            membership = candidate_result.membership
            post = instance.post_result.post
            election = membership.extra.election

            source = instance.review_source
            if not source:
                source = instance.source

            change_metadata = get_change_metadata(
                request, source
            )


            if candidate_result.is_winner:
                membership.extra.elected = True
                membership.extra.save()


                ResultEvent.objects.create(
                    election=election,
                    winner=membership.person,
                    winner_person_name=membership.person.name,
                    post_id=post.extra.slug,
                    post_name=post.label,
                    winner_party_id=membership.on_behalf_of.extra.slug,
                    source=source,
                    user=instance.reviewed_by,
                )

                membership.person.extra.record_version(change_metadata)
                membership.person.save()

                LoggedAction.objects.create(
                    user=instance.reviewed_by,
                    action_type='set-candidate-elected',
                    popit_person_new_version=change_metadata['version_id'],
                    person=membership.person,
                    source=source,
                )
            else:
                change_metadata['information_source'] = \
                    'Setting as "not elected" by implication'
                membership.person.extra.record_version(change_metadata)
                membership.extra.elected = False
                membership.extra.save()
    def save(self):
        instance = super(ReviewVotesForm, self).save(commit=True)

        if instance.review_status == CONFIRMED_STATUS:
            with transaction.atomic():
                self.mark_candidates_as_winner(self.request, instance)

        return instance




class ResultSetForm(forms.ModelForm):
    class Meta:
        model = ResultSet
        fields = (
            'num_turnout_reported',
            'num_spoilt_ballots',
            'source',
        )

    def __init__(self, post_result, *args, **kwargs):
        self.post = post_result.post
        self.post_result = post_result
        self.memberships = []

        initial_values = {}
        for k, v in kwargs.items():
            if k.startswith('initial-'):
                new_k = k.replace('initial-', '')
                initial_values[new_k] = v
                del kwargs[k]

        super(ResultSetForm, self).__init__(*args, **kwargs)

        self.fields['num_spoilt_ballots'].required = False
        self.fields['num_spoilt_ballots'].label += " (Not required)"
        self.fields['num_turnout_reported'].required = False
        self.fields['num_turnout_reported'].label += " (Not required)"

        existing_fields = self.fields
        fields = OrderedDict()

        memberships = self.post.memberships.all()
        memberships = sorted(
            memberships,
            key=lambda member: member.person.name.split(' ')[-1]
        )
        for membership in memberships:
            name = 'memberships_%d' % membership.person.pk

            fields[name] =  forms.IntegerField(
                label="{} ({})".format(
                    membership.person.name,
                    membership.on_behalf_of.name,
                )
            )
            self.memberships.append((membership, name))

        self.fields = fields
        self.fields.update(existing_fields)

        for field in self.fields:
            self.fields[field].initial = initial_values.get(field)


    def mark_candidates_as_winner(self, request, instance):
        for candidate_result in instance.candidate_results.all():
            membership = candidate_result.membership
            post = instance.post_result.post
            election = membership.extra.election

            source = instance.review_source
            if not source:
                source = instance.source

            change_metadata = get_change_metadata(
                request, source
            )


            if candidate_result.is_winner:
                membership.extra.elected = True
                membership.extra.save()


                ResultEvent.objects.create(
                    election=election,
                    winner=membership.person,
                    winner_person_name=membership.person.name,
                    post_id=post.extra.slug,
                    post_name=post.label,
                    winner_party_id=membership.on_behalf_of.extra.slug,
                    source=source,
                    user=instance.reviewed_by,
                )

                membership.person.extra.record_version(change_metadata)
                membership.person.save()

                LoggedAction.objects.create(
                    user=instance.reviewed_by,
                    action_type='set-candidate-elected',
                    popit_person_new_version=change_metadata['version_id'],
                    person=membership.person,
                    source=source,
                )
            else:
                change_metadata['information_source'] = \
                    'Setting as "not elected" by implication'
                membership.person.extra.record_version(change_metadata)
                membership.extra.elected = False
                membership.extra.save()


    def save(self, request):
        instance = super(ResultSetForm, self).save(commit=False)
        instance.post_result = self.post_result
        instance.user = request.user if \
            request.user.is_authenticated() else None
        instance.ip_address = get_client_ip(request)
        instance.save(request)

        winner_count = self.memberships[0][0]\
            .extra.election.postextraelection_set.filter(
                postextra=self.memberships[0][0].post.extra)[0].winner_count

        winners = dict(sorted(
            [("{}-{}".format(self[y].value(), x.person.id), x)
                for x, y in self.memberships],
            reverse=True,
            key=lambda votes: int(votes[0].split('-')[0])
        )[:winner_count])

        for membership, field_name in self.memberships:
            instance.candidate_results.create(
                membership=membership,
                is_winner=bool(membership in winners.values()),
                num_ballots_reported=self[field_name].value(),
            )

        if instance.review_status == CONFIRMED_STATUS:
            with transaction.atomic():
                self.mark_candidates_as_winner(request, instance)

        return instance
