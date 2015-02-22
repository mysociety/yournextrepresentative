from requests.adapters import ConnectionError
from slumber.exceptions import HttpServerError, HttpClientError

from django.http import Http404
from django.shortcuts import render

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
