# -*- coding: utf-8 -*-

from django import forms
from django.core.exceptions import ValidationError

from candidates.mapit import BaseMapItException
from popolo.models import Area

from .mapit import get_wmc_from_postcode

class PostcodeForm(forms.Form):
    postcode = forms.CharField(
        label='Enter your postcode',
        max_length=20
    )

    def clean_postcode(self):
        postcode = self.cleaned_data['postcode']
        try:
            # Go to MapIt to check if this postcode is valid and
            # contained in a constituency. (If it's valid then the
            # result is cached, so this doesn't cause a double lookup.)
            get_wmc_from_postcode(postcode)
        except BaseMapItException as e:
            raise ValidationError(unicode(e))
        return postcode


class ConstituencyForm(forms.Form):
    constituency = forms.ModelChoiceField(
        label='Select a constituency',
        queryset=Area.objects.filter(extra__type__name='WMC').order_by('name'),
        empty_label='',
    )

    def clean_constituency(self):
        constituency = self.cleaned_data['constituency']
        if constituency == 'none':
            raise ValidationError("You must select a constituency")
        return constituency
