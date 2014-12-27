# This module contains get_mapit_cached to do MapIt postcode lookups,
# but caching the results using the generic Django cache.

import re

import requests

from django.conf import settings
from django.core.cache import cache
from django.utils.http import urlquote

class BaseMapItException(Exception):
    pass

class BadPostcodeException(BaseMapItException):
    pass

class NoConstituencyForPostcodeException(BaseMapItException):
    pass

class UnknownMapitException(BaseMapItException):
    pass

def get_wmc_from_postcode(original_postcode):
    postcode = re.sub(r'\s*', '', original_postcode.lower())
    cached_result = cache.get(postcode)
    if cached_result:
        return cached_result
    url = 'http://mapit.mysociety.org/postcode/' + urlquote(postcode)
    r = requests.get(url)
    if r.status_code == 200:
        mapit_result = r.json()
        wmc = mapit_result.get('shortcuts', {}).get('WMC')
        if not wmc:
            raise NoConstituencyForPostcodeException(
                u'No constituency found for the postcode "{0}"'.format(
                    original_postcode
                )
            )
        cache.set(postcode, wmc, settings.MAPIT_CACHE_SECONDS)
        return wmc
    elif r.status_code == 400:
        mapit_result = r.json()
        raise BadPostcodeException(mapit_result['error'])
    elif r.status_code == 404:
        raise BadPostcodeException(
            u'The postcode "{0}" couldn\'t be found'.format(original_postcode)
        )
    else:
        raise UnknownMapitException(
            u'Unknown MapIt error for postcode "{0}"'.format(
                original_postcode
            )
        )
