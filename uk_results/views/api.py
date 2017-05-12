from rest_framework import serializers, viewsets, filters

from django.db.models import Prefetch

import django_filters
from django_filters.widgets import BooleanWidget

from candidates.serializers import OrganizationExtraSerializer
from candidates.views import ResultsSetPagination

from ..serializers import (
    CandidateResultSerializer, PostElectionResultSerializer, ResultSetSerializer
)
from ..models import (
    CandidateResult, CouncilElection, CouncilElectionResultSet,
    PostElectionResult, ResultSet,
)


class CouncilElectionResultSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouncilElectionResultSet
        fields = (
            'noc',
            'controller',
        )
        depth = 5

    controller = OrganizationExtraSerializer(
        many=False, read_only=True, source='controller.extra')


class CouncilElectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouncilElection
        fields = (
            'council',
            'council_name',
            'election',
            'confirmed_controlling_party',
            'confirmed',
            'reported_results',
            )
        depth = 5

    election = serializers.SerializerMethodField()
    council_name = serializers.SerializerMethodField()
    confirmed_controlling_party = serializers.SerializerMethodField()
    confirmed = serializers.SerializerMethodField()
    reported_results = CouncilElectionResultSetSerializer(many=True, read_only=True)

    def get_election(self, obj):
        return obj.election.slug

    def get_council_name(self, obj):
        return obj.council.name

    def get_confirmed(self, obj):
        return bool(obj.reported_results.all().confirmed())

    def get_confirmed_controlling_party(self, obj):
        confirmed = obj.reported_results.all().confirmed()
        if confirmed and confirmed.first().controller:
            return OrganizationExtraSerializer(
                context={'request': self.context['request']}
                ).to_representation(
                    confirmed.first().controller.extra,
                )


class CouncilElectionIsConfirmedFilter(django_filters.FilterSet):
    confirmed = django_filters.BooleanFilter(widget=BooleanWidget())

    class Meta:
        model = CouncilElection
        fields = ['confirmed',]

class CouncilElectionViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_value_regex="(?!\.json$)[^/]+"
    serializer_class = CouncilElectionSerializer
    queryset = CouncilElection.objects.all()
    lookup_field = 'election__slug'

    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = CouncilElectionIsConfirmedFilter


class CandidateResultViewSet(viewsets.ModelViewSet):
    queryset = CandidateResult.objects \
        .select_related(
            'membership__on_behalf_of__extra',
            'membership__organization__extra',
            'membership__post__extra',
            'membership__extra__election',
            'membership__person',
        ) \
        .order_by('id')
    serializer_class = CandidateResultSerializer
    pagination_class = ResultsSetPagination


class ResultSetViewSet(viewsets.ModelViewSet):
    queryset = ResultSet.objects \
        .select_related(
            'post_election_result__post_election__postextra',
            'user',
        ) \
        .order_by('id')
    serializer_class = ResultSetSerializer
    pagination_class = ResultsSetPagination

    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ['review_status',]



class PostElectionResultViewSet(viewsets.ModelViewSet):
    queryset = PostElectionResult.objects \
        .select_related('post_election__postextra') \
        .prefetch_related(
            Prefetch(
                'result_sets',
                ResultSet.objects.select_related(
                    'post_election_result__post_election__postextra',
                    'user',
                ) \
                .prefetch_related(
                    Prefetch(
                        'candidate_results',
                        CandidateResult.objects.select_related(
                            'membership__on_behalf_of__extra',
                            'membership__organization__extra',
                            'membership__post__extra',
                            'membership__extra__election',
                            'membership__person',
                        )
                    )
                )
            ),
        ) \
        .order_by('id')
    serializer_class = PostElectionResultSerializer
    pagination_class = ResultsSetPagination
    filter_fields = ('confirmed',)
