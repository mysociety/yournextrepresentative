from django.views.generic import RedirectView


class ConstituenciesRedirect(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        return '/election/2015/constituencies' + kwargs['list_filter']


class ConstituencyRedirect(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        return '/election/2015/post/' + kwargs['rest_of_path']


class PartyRedirect(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        return '/election/2015/part' + kwargs['rest_of_path']


class CandidacyRedirect(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        return '/election/2015/candidacy' + kwargs['rest_of_path']


class PersonCreateRedirect(RedirectView):

    def get_redirect_url(self, *args, **kwargs):
        return '/election/2015/person/create/'
