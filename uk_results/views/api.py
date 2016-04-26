from rest_framework import serializers, viewsets, filters
import django_filters
from django_filters.widgets import BooleanWidget

from candidates.serializers import OrganizationExtraSerializer

from ..models import CouncilElection, CouncilElectionResultSet


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
        if confirmed:
            return OrganizationExtraSerializer(
                context={'request': self.context['request']}
                ).to_representation(
                    confirmed.first().controller.extra,
                )


class IsConfirmedFilter(django_filters.FilterSet):
    confirmed = django_filters.BooleanFilter(widget=BooleanWidget())

    class Meta:
        model = CouncilElection
        fields = ['confirmed']

class CouncilElectionViewSet(viewsets.ReadOnlyModelViewSet):
    lookup_value_regex="(?!\.json$)[^/]+"
    serializer_class = CouncilElectionSerializer
    queryset = CouncilElection.objects.all()
    lookup_field = 'election__slug'

    filter_backends = (filters.DjangoFilterBackend,)
    # filter_fields = ('confirmed',)
    filter_class = IsConfirmedFilter
