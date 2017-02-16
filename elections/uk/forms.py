# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import forms
from django.core.exceptions import ValidationError

from candidates.mapit import BaseMapItException, BadPostcodeException
from popolo.models import Area

from compat import text_type

from .mapit import get_areas_from_postcode

class PostcodeForm(forms.Form):
    q = forms.CharField(
        label='Enter a candidate name or postcode',
        max_length=200,
        widget=forms.TextInput(attrs={'placeholder': 'Enter a name'})
    )

    def clean_q(self):
        postcode = self.cleaned_data['q']
        try:
            # Go to MapIt to check if this postcode is valid and
            # contained in a constituency. (If it's valid then the
            # result is cached, so this doesn't cause a double lookup.)
            get_areas_from_postcode(postcode)
        except (BaseMapItException, BadPostcodeException) as e:
            raise ValidationError(text_type(e))
        return postcode
