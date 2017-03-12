# coding=utf-8
from __future__ import unicode_literals

import requests

from django.conf import settings
from django.utils.http import urlquote
from django.core.cache import cache
from django.utils.six.moves.urllib_parse import urljoin
from django.utils.translation import ugettext as _

from elections.models import AreaType


class BaseMapItException(Exception):
    pass


class BadPostcodeException(BaseMapItException):
    pass


class BadCoordinatesException(BaseMapItException):
    pass


class UnknownMapitException(BaseMapItException):
    pass


def fetch_area_ids(**kwargs):
    if kwargs['postcode']:
        areas = get_areas_from_postcode(kwargs['postcode'])

    if kwargs['coords']:
        areas = get_areas_from_coords(kwargs['coords'])

    return areas

def format_code_from_area(area):
    code = None
    if 'gss' in area['codes']:
        code = str('gss:' + area['codes']['gss'])
    elif 'ons' in area['codes']:
        code = str('ons:' + area['codes']['ons'])
    elif 'unit_id' in area['codes']:
        code = str('unit_id:' + area['codes']['unit_id'])
    elif 'police_id' in area['codes']:
        code = str('police:' + area['codes']['police_id'])
    elif 'osni_oid' in area['codes']:
        code = str('osni_oid:' + area['codes']['osni_oid'])
    return code


def get_known_area_types(mapit_result):
        known_area_types = set(AreaType.objects.values_list('name', flat=True))
        return [
            (a['type'], str(a['id']))
            for a in mapit_result.values()
            if a['type'] in known_area_types
        ]


def get_areas_from_postcode(postcode):
    cache_key = 'mapit-postcode:' + postcode
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    url = urljoin(settings.MAPIT_BASE_URL, '/postcode/' + urlquote(postcode))
    r = requests.get(url)
    if r.status_code == 200:
        mapit_result = r.json()
        areas = get_known_area_types(mapit_result['areas'])
        cache.set(cache_key, areas, settings.MAPIT_CACHE_SECONDS)
        return areas
    elif r.status_code == 400:
        mapit_result = r.json()
        raise BadPostcodeException(mapit_result['error'])
    elif r.status_code == 404:
        raise BadPostcodeException(
            _('The postcode “{0}” couldn’t be found').format(
                postcode
            )
        )
    else:
        raise UnknownMapitException(
            _('Unknown MapIt error for postcode "{0}"').format(
                postcode
            )
        )


def get_areas_from_coords(coords):
    url = urljoin(
        settings.MAPIT_BASE_URL,
        '/point/4326/' + urlquote(coords)
        )

    cache_key = 'mapit-postcode:' + coords
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result

    r = requests.get(url)
    if r.status_code == 200:
        mapit_result = r.json()
        areas = get_known_area_types(mapit_result)
        cache.set(url, areas, settings.MAPIT_CACHE_SECONDS)
        return areas
    elif r.status_code == 400:
        mapit_result = r.json()
        raise BadCoordinatesException(mapit_result['error'])
    elif r.status_code == 404:
        raise BadCoordinatesException(
            'The coordinates "{0}" could not be found'.format(
                coords
            )
        )
    else:
        raise UnknownMapitException(
            'Unknown MapIt error for coordinates "{0}"'.format(
                coords
            )
        )
