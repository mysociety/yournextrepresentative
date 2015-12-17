import json
from os.path import dirname
import subprocess
import sys

import django
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch
from django.http import HttpResponse
from django.views.generic import View

from candidates.models import LoggedAction, OrganizationExtra
from elections.models import AreaType, Election
from popolo.models import Area, Membership, Person
from rest_framework import viewsets

from candidates.models import PostExtra
from candidates import serializers


class VersionView(View):

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        result = {
            'python_version': sys.version,
            'django_version': django.get_version(),
            'interesting_user_actions': LoggedAction.objects \
                .exclude(action_type='set-candidate-not-elected') \
                .count(),
            'users_who_have_edited': User.objects \
                .annotate(edit_count=Count('loggedaction')) \
                .filter(edit_count__gt=0).count()
        }
        # Try to get the object name of HEAD from git:
        try:
            git_version = subprocess.check_output(
                ['git', 'rev-parse', '--verify', 'HEAD'],
                cwd=dirname(__file__),
            ).strip()
            result['git_version'] = git_version
        except OSError, subprocess.CalledProcessError:
            pass
        return HttpResponse(
            json.dumps(result), content_type='application/json'
        )


class PostIDToPartySetView(View):

    http_method_names = ['get']

    def get(self, request, *args, **kwargs):
        result = dict(
            PostExtra.objects.filter(elections__current=True) \
               .values_list('slug', 'party_set__slug')
        )
        return HttpResponse(
            json.dumps(result), content_type='application/json'
        )


# Now the django-rest-framework based API views:

class PersonViewSet(viewsets.ModelViewSet):
    queryset = Person.objects \
        .select_related('extra') \
        .prefetch_related(
            Prefetch(
                'memberships',
                Membership.objects.select_related(
                    'on_behalf_of__extra',
                    'organization__extra',
                    'post__extra',
                    'extra',
                )
            ),
            'memberships__extra__election',
            'memberships__organization__extra',
            'extra__images',
            'other_names',
            'contact_details',
            'links',
            'identifiers',
        ) \
        .order_by('sort_name')
    serializer_class = serializers.PersonSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = OrganizationExtra.objects \
        .select_related('base') \
        .prefetch_related(
            'images',
            'images__extra',
            'base__contact_details',
            'base__other_names',
            'base__sources',
            'base__links',
            'base__identifiers',
            'base__parent',
            'base__parent__extra',
        ) \
        .order_by('base__name')
    lookup_field = 'slug'
    serializer_class = serializers.OrganizationExtraSerializer


class PostViewSet(viewsets.ModelViewSet):
    queryset = PostExtra.objects \
        .select_related(
            'base__organization__extra',
            'base__area__extra',
        ) \
        .prefetch_related(
            'elections',
            'elections__area_types',
            'base__area__other_identifiers',
            'base__memberships',
        ) \
        .order_by('base__label')
    lookup_field = 'slug'
    serializer_class = serializers.PostExtraSerializer


class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects \
        .prefetch_related('extra') \
        .order_by('name')
    serializer_class = serializers.AreaSerializer


class AreaTypeViewSet(viewsets.ModelViewSet):
    queryset = AreaType.objects.all()
    serializer_class = serializers.AreaTypeSerializer


class ElectionViewSet(viewsets.ModelViewSet):
    queryset = Election.objects.all()
    lookup_field = 'slug'
    serializer_class = serializers.ElectionSerializer
