# If you need to define any forms specific to this country's site, put
# those definitions here.

from __future__ import unicode_literals
from django import forms

from candidates.models.address import check_address

from candidates.forms import StrippedCharField


class AddressForm(forms.Form):
    address = StrippedCharField(
        label='Enter your county or constituency',
        max_length=2048,
    )

    def __init__(self, country, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        self.country = country

    def clean_address(self):
        address = self.cleaned_data['address']
        check_address(address, self.country)
        return address
