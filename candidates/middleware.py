import re

from requests.adapters import ConnectionError
from slumber.exceptions import HttpServerError, HttpClientError

from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils.http import urlquote

class PopItDownMiddleware(object):

    def process_exception(self, request, exc):
        popit_down = False
        if isinstance(exc, ConnectionError):
            popit_down = True
        elif isinstance(exc, HttpServerError) and '503' in unicode(exc):
            popit_down = True
        if popit_down:
            return render(request, 'candidates/popit_down.html', status=503)
        message_404 = 'Client Error 404' in unicode(exc)
        if isinstance(exc, HttpClientError) and message_404:
            raise Http404()
        return None


class CopyrightAssignmentMiddleware(object):
    """Check that authenticated users have agreed to copyright assigment

    This must come after AuthenticationMiddleware so that request.user
    is present.

    If this is an authenticated user, then insist that they agree to
    assign copyright of any conributions to Democracy Club
    """

    EXCLUDED_PATHS = (
        re.compile(r'^/copyright-question'),
        re.compile(r'^/accounts/'),
        re.compile(r'^/admin/'),
    )

    def process_request(self, request):
        for path_re in self.EXCLUDED_PATHS:
            if path_re.search(request.path):
                return None
        if not request.user.is_authenticated():
            return None
        already_assigned = request.user.terms_agreement.assigned_to_dc
        if already_assigned:
            return None
        else:
            # Then redirect to a view that asks you to assign
            # copyright:
            assign_copyright_url = reverse('ask-for-copyright-assignment')
            assign_copyright_url += "?next={0}".format(
                urlquote(request.path)
            )
            return HttpResponseRedirect(assign_copyright_url)
