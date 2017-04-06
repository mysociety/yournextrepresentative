from __future__ import unicode_literals
import random

from django.views.generic import RedirectView

from candidates.models import PostExtraElection
from elections.uk.lib import is_valid_postcode


class ConstituenciesRedirect(RedirectView):

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        return '/election/2015/constituencies' + kwargs['list_filter']


class ConstituencyRedirect(RedirectView):

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        return '/election/2015/post/' + kwargs['rest_of_path']


class PartyRedirect(RedirectView):

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        return '/election/2015/part' + kwargs['rest_of_path']


class CandidacyRedirect(RedirectView):

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        return '/election/2015/candidacy' + kwargs['rest_of_path']


class PersonCreateRedirect(RedirectView):

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        return '/election/2015/person/create/'


class CachedCountsRedirect(RedirectView):

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        if kwargs['rest_of_path'] == 'constituencies':
            new_rest_of_path = 'posts'
        else:
            new_rest_of_path = 'parties'
        return '/numbers/election/2015/' + new_rest_of_path

class OfficialDocumentsRedirect(RedirectView):

    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        return '/upload_document/upload/election/2015/post/' + kwargs['rest_of_path']


class WhoPostcodeRedirect(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        postcode = self.request.GET.get('postcode', '')
        if is_valid_postcode(postcode):
            return "https://whocanivotefor.co.uk/elections/{}".format(postcode)
        else:
            return "/?who_postcode={}&postcode_invalid=1".format(postcode)


class HelpOutCTAView(RedirectView):

    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        pe_qs = PostExtraElection.objects.filter(
            election__current=True,
            postextra__suggestedpostlock=None
            ).exclude(postextra__candidates_locked=True)

        if pe_qs:
            random_offset = random.randrange(min(50, pe_qs.count()))
            postextra_election = pe_qs[random_offset]
            return "/bulk_adding/{}/{}/".format(
                postextra_election.election.slug,
                postextra_election.postextra.slug
            )
        return "/?get_involved_link=1"
