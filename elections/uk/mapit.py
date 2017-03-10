# coding=utf-8

from __future__ import unicode_literals

import re
import logging

import requests

from django.conf import settings
from django.core.cache import cache
from django.utils.http import urlquote
from django.utils.six.moves.urllib_parse import urljoin
from django.utils.translation import ugettext as _

from candidates.mapit import (
    BaseMapItException, BadPostcodeException,
    UnknownMapitException, BadCoordinatesException
)
from popolo.models import Area


logger = logging.getLogger(__name__)

EE_BASE_URL = getattr(
    settings, "EE_BASE_URL", "https://elections.democracyclub.org.uk/")


class NoConstituencyForPostcodeException(BaseMapItException):
    pass


class MapItAreaNotFoundException(BaseMapItException):
    pass


def get_known_area_types(ee_areas):
    result = []
    for election in ee_areas['results']:
        if election['group_type'] == 'election':
            continue
        if election['group_type'] == 'organisation':
            area_type = election['organisation']['organisation_type']
            area_id = ":".join(
                [area_type, election['organisation']['official_identifier']])
        else:
            area_id = election['division']['official_identifier']
            area_type = election['division']['division_type']
        result.append((
            area_type,
            area_id
        ))

    area_ids = [r[1] for r in result]
    known_areas = Area.objects.filter(identifier__in=area_ids)

    return [(a.extra.type.name,a.identifier) for a in known_areas]


def get_areas(url, cache_key, exception):
    r = requests.get(url)
    if r.status_code == 200:
        ee_result = r.json()
        result = get_known_area_types(ee_result)
        cache.set(cache_key, result, settings.MAPIT_CACHE_SECONDS)
        return result
    elif r.status_code == 400:
        ee_result = r.json()
        raise exception(ee_result['error'])
    elif r.status_code == 404:
        raise exception(
            _('The url "{}" couldn’t be found').format(url)
        )
    else:
        raise UnknownMapitException(
            _('Unknown error for "{0}"').format(
                url
            )
        )


def get_areas_from_postcode(original_postcode):
    postcode = re.sub(r'(?ms)\s*', '', original_postcode.lower())
    if re.search(r'[^a-z0-9]', postcode):
        raise BadPostcodeException(
            _('There were disallowed characters in "{0}"').format(
                original_postcode)
        )
    cache_key = 'mapit-postcode:' + postcode
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    url = urljoin(EE_BASE_URL, "/api/elections/?postcode={0}".format(
        urlquote(postcode)))
    try:
        areas = get_areas(url, cache_key, BadPostcodeException)
    except BadPostcodeException:
        # Give a nicer error message, as this is used on the frontend
        raise BadPostcodeException(
            'The postcode “{}” couldn’t be found'.format(original_postcode))
    return areas


def get_areas_from_coords(coords):
    url = urljoin(EE_BASE_URL, "/api/elections/?coords={0}".format(
        urlquote(coords)))

    cache_key = 'mapit-postcode:' + coords
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    return get_areas(url, cache_key, BadCoordinatesException)
