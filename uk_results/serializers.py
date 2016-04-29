from __future__ import unicode_literals

from rest_framework import serializers

from .models import PostResult, ResultSet, CandidateResult

from candidates.serializers import (
    MembershipSerializer, MinimalPostExtraSerializer
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
            'user', 'user_id',
        )
    # post_result = PostResultSerializer()
    user = serializers.ReadOnlyField(source='user.username')
    user_id = serializers.ReadOnlyField(source='user.id')
    candidate_results = CandidateResultSerializer(many=True, read_only=True)


class PostResultSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = PostResult
        fields = (
            'id', 'url',
            'confirmed',
            'post',
            'result_sets',
        )
    post = MinimalPostExtraSerializer(source='post.extra')
    result_sets = ResultSetSerializer(many=True)
