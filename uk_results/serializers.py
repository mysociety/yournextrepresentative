from __future__ import unicode_literals

from rest_framework import serializers

from .models import PostElectionResult, ResultSet, CandidateResult

from candidates.serializers import (
    MembershipSerializer, EmbeddedPostElectionSerializer
)


class CandidateResultSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = CandidateResult
        fields = (
            'id', 'url',
            'membership',
            'result_set',
            'num_ballots_reported', 'is_winner',
        )

    membership = MembershipSerializer(read_only=True)
    # result_set = ResultSetSerializer(read_only=True)


class ResultSetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ResultSet
        fields = (
            'id', 'url',
            'candidate_results',
            'ip_address',
            'num_turnout_reported', 'num_spoilt_ballots',
            # 'post_result',
            'user', 'user_id', 'review_status',
        )
    # post_result = PostResultSerializer()
    user = serializers.ReadOnlyField(source='user.username')
    user_id = serializers.ReadOnlyField(source='user.id')
    candidate_results = CandidateResultSerializer(many=True, read_only=True)


class PostElectionResultSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PostElectionResult
        fields = (
            'id', 'url',
            'confirmed',
            'post_election',
            'result_sets',
        )
    post_election = EmbeddedPostElectionSerializer()
    result_sets = ResultSetSerializer(many=True)
