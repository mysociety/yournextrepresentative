from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from haystack.generic_views import SearchView

from elections.uk.lib import is_valid_postcode


class PersonSearch(SearchView):
    def get(self, request, *args, **kwargs):
        ret = super(PersonSearch, self).get(request, *args, **kwargs)
        context = self.get_context_data(**ret.context_data)

        if context['looks_like_postcode']:
            if not context['object_list']:
                # This looks like a postcode, and we've found nothing else
                # so redirect to a postcode view.
                home_page = reverse('lookup-postcode')
                return HttpResponseRedirect("{0}?postcode={1}".format(
                    home_page,
                    context['query']
                ))

        return ret

    def get_context_data(self, **kwargs):
        context = super(PersonSearch, self).get_context_data(**kwargs)
        context['looks_like_postcode'] = is_valid_postcode(context['query'])
        # Only return 5 results
        context['object_list'] = context['object_list'][:5]
        return context
