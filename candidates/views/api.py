import json
from os.path import dirname
import subprocess
import sys

import django
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import HttpResponse
from django.views.generic import View

from candidates.models import LoggedAction
from elections.models import Election
from popolo.models import Area, Organization, Person, Post
from rest_framework import filters, viewsets

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
        .prefetch_related('extra') \
        .order_by('sort_name')
    serializer_class = serializers.PersonSerializer


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects \
        .prefetch_related('extra') \
        .order_by('name')
    serializer_class = serializers.OrganizationSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('extra__slug',)


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects \
        .prefetch_related('extra', 'extra__elections') \
        .order_by('label')
    serializer_class = serializers.PostSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('extra__slug',)


class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects \
        .prefetch_related('extra') \
        .order_by('name')
    serializer_class = serializers.AreaSerializer


class ElectionViewSet(viewsets.ModelViewSet):
    queryset = Election.objects.all()
    serializer_class = serializers.ElectionSerializer
