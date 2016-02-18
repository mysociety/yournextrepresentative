# coding=utf-8

from __future__ import unicode_literals

import re
import logging

import requests

from django.conf import settings
from django.core.cache import cache
from django.utils.http import urlquote
from django.utils.translation import ugettext as _

from candidates.mapit import (
    BaseMapItException, BadPostcodeException, UnknownMapitException
)
from elections.models import AreaType


logger = logging.getLogger(__name__)


class NoConstituencyForPostcodeException(BaseMapItException):
    pass


class MapItAreaNotFoundException(BaseMapItException):
    pass


UK_AREA_ORDER = ['SPC', 'SPE', 'WAC', 'WAE', 'NIE', 'LAC', 'GLA', 'WMC']


def area_sort_key(type_and_id_tuple):
    try:
        return UK_AREA_ORDER.index(type_and_id_tuple[0])
    except ValueError:
        return len(UK_AREA_ORDER)


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


def get_areas_from_postcode(original_postcode):
    postcode = re.sub(r'(?ms)\s*', '', original_postcode.lower())
    if re.search(r'[^a-z0-9]', postcode):
        raise BadPostcodeException(
            _('There were disallowed characters in "{0}"').format(original_postcode)
        )
    cache_key = 'mapit-postcode:' + postcode
    cached_result = cache.get(cache_key)
    if cached_result:
        return cached_result
    url = '{0}/postcode/{1}'.format(
        settings.MAPIT_BASE_URL,
        urlquote(postcode))
    r = requests.get(url)
    if r.status_code == 200:
        mapit_result = r.json()
        known_area_types = set(AreaType.objects.values_list('name', flat=True))

        result = sorted(
            [
                (a['type'], format_code_from_area(a))
                for a in mapit_result['areas'].values()
                if a['type'] in known_area_types
            ],
            key=area_sort_key
        )

        cache.set(cache_key, result, settings.MAPIT_CACHE_SECONDS)
        return result
    elif r.status_code == 400:
        mapit_result = r.json()
        raise BadPostcodeException(mapit_result['error'])
    elif r.status_code == 404:
        raise BadPostcodeException(
            _('The postcode “{0}” couldn’t be found').format(original_postcode)
        )
    else:
        raise UnknownMapitException(
            _('Unknown MapIt error for postcode "{0}"').format(
                original_postcode
            )
        )



def get_wmc_from_postcode(original_postcode):
    postcode = re.sub(r'(?ms)\s*', '', original_postcode.lower())
    if re.search(r'[^a-z0-9]', postcode):
        raise BadPostcodeException(
            _('There were disallowed characters in "{0}"').format(original_postcode)
        )
    cached_result = cache.get(postcode)
    if cached_result:
        return cached_result
    url = '{0}/postcode/{1}'.format(
        settings.MAPIT_BASE_URL,
        urlquote(postcode))
    r = requests.get(url)
    if r.status_code == 200:
        mapit_result = r.json()
        wmc = mapit_result.get('shortcuts', {}).get('WMC')
        if not wmc:
            raise NoConstituencyForPostcodeException(
                _('No constituency found for the postcode "{0}"').format(
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
            _('The postcode “{0}” couldn’t be found').format(original_postcode)
        )
    else:
        raise UnknownMapitException(
            _('Unknown MapIt error for postcode "{0}"').format(
                original_postcode
            )
        )


class MapitLookup(dict):
    def __init__(self, initial_codes=(),
                 mapit_base_url=settings.MAPIT_BASE_URL):
        self.mapit_base_url = mapit_base_url
        for code in initial_codes:
            self.load_data(code)

    def load_data(self, code):
        data = requests.get("{mapit_base_url}areas/{code}".format(
            mapit_base_url=self.mapit_base_url, code=code
        )).json()
        self.update(data)

    def __getitem__(self, key):
        key = str(key)
        try:
            return super(MapitLookup, self).__getitem__(key)
        except KeyError:
            try:
                logging.info("Making extra request to Mapit for ID {0}".format(
                    key
                ))
                url = urljoin(self.mapit_base_url,
                              "area/{key}".format(key=key))
                req = requests.get(url)
                if req.status_code == 404 or \
                        req.json()[key].get('code', 200) == 404:
                    raise MapItAreaNotFoundException
                self.update({key: req.json()})
                return self[key]
            except MapItAreaNotFoundException:
                raise KeyError
            except Exception:
                raise
