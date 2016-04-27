# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from collections import OrderedDict

from django import forms

from popolo.models import Organization

from models import CouncilElectionResultSet, ResultSet


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
    )

    def clean(self, **kwargs):
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

        super(ResultSetForm, self).__init__(*args, **kwargs)
        existing_fields = self.fields
        fields = OrderedDict()

        for membership in self.post.memberships.all():
            name = 'memberships_%d' % membership.person.pk

            fields[name] =  forms.IntegerField(
                label=membership.person.name
            )
            self.memberships.append((membership, name))

        self.fields = fields
        self.fields.update(existing_fields)

    def save(self, request):
        instance = super(ResultSetForm, self).save(commit=False)
        instance.post_result = self.post_result
        instance.user = request.user if \
            request.user.is_authenticated() else None
        instance.ip_address = request.META['REMOTE_ADDR']
        instance.save()

        winer_count = self.memberships[0][0]\
            .extra.election.postextraelection_set.filter(
                postextra=self.memberships[0][0].post.extra)[0].winner_count

        winner = max((self[y].value(), x) for x, y
            in self.memberships)[winer_count]

        for membership, field_name in self.memberships:
            instance.candidate_results.create(
                membership=membership,
                is_winner=bool(membership == winner),
                num_ballots_reported=self[field_name].value(),
            )

        return instance
