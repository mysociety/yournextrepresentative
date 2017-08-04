# If you need to define any views specific to this country's site, put
# those definitions here.

from __future__ import unicode_literals

from candidates.views import AddressFinderView

from .forms import AddressForm


class KenyaFrontpage(AddressFinderView):
    form_class = AddressForm
