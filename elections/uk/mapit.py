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
    BaseMapItException, BadPostcodeException, UnknownMapitException
)
from popolo.models import Area


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
    url = urljoin(settings.MAPIT_BASE_URL,
                  '/postcode/{0}'.format(urlquote(postcode)))
    r = requests.get(url)
    if r.status_code == 200:
        mapit_result = r.json()
        result = []
        for mapit_area in mapit_result['areas'].values():
            areas = Area.objects.filter(
                    extra__type__name=mapit_area['type'],
                    identifier=format_code_from_area(mapit_area)
            )

            if areas.exists():
                is_no_data_area = False
                for area in areas:
                    for child_area in area.children.all():
                        if child_area.identifier.startswith('NODATA:'):
                            is_no_data_area = True
                            break

                if is_no_data_area:
                    area_type = "NODATA"
                else:
                    area_type = mapit_area['type']

                result.append((
                    area_type,
                    format_code_from_area(mapit_area))
                )

        result = sorted(result, key=area_sort_key)

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
    url = urljoin(settings.MAPIT_BASE_URL,
                  '/postcode/{0}'.format(urlquote(postcode)))
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
        data = requests.get(urljoin(self.mapit_base_url, "areas/{code}".format(
            mapit_base_url=self.mapit_base_url, code=code
        ))).json()
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
