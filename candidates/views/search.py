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


class PersonSearch(SearchView):
    form_class = PersonSearchForm
