from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.html import escape

from haystack.generic_views import SearchView
from haystack.forms import SearchForm


class PersonSearchForm(SearchForm):
    """
    When Haystack indexed things into its sythesized text field
    it HTML escapes everything. This means that we also need to
    escape our search terms as otherwise names with apostrophes
    and the like never match as the entry in the search index
    is O&#39;Reilly and our search term is O'Reilly
    """
    def clean_q(self):
        return escape(self.cleaned_data['q'])

from elections.uk.lib import is_valid_postcode


class PersonSearch(SearchView):

    form_class = PersonSearchForm

    def get(self, request, *args, **kwargs):
        ret = super(PersonSearch, self).get(request, *args, **kwargs)
        context = self.get_context_data(**ret.context_data)

        if context['looks_like_postcode']:
            if not context['object_list']:
                # This looks like a postcode, and we've found nothing else
                # so redirect to a postcode view.
                home_page = reverse('lookup-postcode')
                return HttpResponseRedirect("{0}?q={1}".format(
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
