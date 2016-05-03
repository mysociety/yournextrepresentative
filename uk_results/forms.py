# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from collections import OrderedDict

from django import forms

from popolo.models import Organization
from candidates.views.version_data import get_client_ip

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

    def __init__(self, review_result, *args, **kwargs):
        self.post = review_result.post_result.post

        super(ReviewVotesForm, self).__init__(*args, **kwargs)


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

        # TODO sort by last name here
        for membership in self.post.memberships.all():
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

    def save(self, request):
        instance = super(ResultSetForm, self).save(commit=False)
        instance.post_result = self.post_result
        instance.user = request.user if \
            request.user.is_authenticated() else None
        instance.ip_address = get_client_ip(request)
        instance.save()


        winner_count = self.memberships[0][0]\
            .extra.election.postextraelection_set.filter(
                postextra=self.memberships[0][0].post.extra)[0].winner_count

        winners = dict(sorted(
            [(int(self[y].value()), x)
                for x, y in self.memberships],
            reverse=True,
            key=lambda votes: votes[0]
        )[:winner_count])

        for membership, field_name in self.memberships:
            instance.candidate_results.create(
                membership=membership,
                is_winner=bool(membership in winners.values()),
                num_ballots_reported=self[field_name].value(),
            )

        return instance
