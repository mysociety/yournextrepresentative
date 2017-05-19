from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.html import escape

from haystack.query import SearchQuerySet
from haystack.generic_views import SearchView
from haystack.forms import SearchForm


def search_person_by_name(name, sqs=None):
    """
    Becuase the default haystack operator is AND if you search for
    John Quincy Adams then it looks for `John AND Quincy AND Adams'
    and hence won't find John Adams. This results in missed matches
    and duplicates. So if it looks like there's more than two names
    split them and search using the whole name provided or just the
    first and last. This results in
    `(John AND Quincy AND Adams) OR (John AND Adams)` which is a bit
    more tolerant.
    """
    parts = name.split()
    if sqs is None:
        sqs = SearchQuerySet().filter(content=name)
    if len(parts) >= 2:
        short_name = ' '.join([parts[0], parts[-1]])
        sqs = sqs.filter_or(content=short_name)

    return sqs


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

    def search(self):
        sqs = super(PersonSearchForm, self).search()
        return search_person_by_name(self.cleaned_data['q'], sqs)


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
        return context
