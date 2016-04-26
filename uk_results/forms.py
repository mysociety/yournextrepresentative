# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import json

from django import forms

from popolo.models import Organization

from models import CouncilElectionResultSet


class ReportCouncilElectionControlForm(forms.ModelForm):
    class Meta:
        model = CouncilElectionResultSet
        fields = [
            'council_election',
            'controller',
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


class ConfirmControlForm(forms.ModelForm):
    class Meta:
        model = CouncilElectionResultSet
        fields = [
            'confirm_source',
            'confirmed_by',
        ]
        widgets = {
            'confirmed_by': forms.HiddenInput(),
            'confirm_source': forms.Textarea(
                attrs={'rows': 1, 'columns': 72}
            )
        }

    # def __init__(self, *args, **kwargs):
    #     super(ConfirmControlForm, self).__init__(*args, **kwargs)
    #     self.user = user

    # def clean(self, **kwargs):
    #     self.cleaned_data['confirmed_by'] = \
    #         self.user.pk
    #     return self.cleaned_data
