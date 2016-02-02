# -*- coding: utf-8 -*-

from django import forms
from django.utils.translation import ugettext_lazy as _

from popolo.models import Area


class ConstituencySelectorForm(forms.Form):

    cons_area_id = forms.ModelChoiceField(
        label=_('Select your constituency'),
        empty_label='',
        to_field_name='identifier',
        queryset=Area.objects.all()
    )
