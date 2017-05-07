from django.conf import settings
from django.shortcuts import get_object_or_404

from braces.views import UserPassesTestMixin
from auth_helpers.views import user_in_group

from candidates.models import PostExtraElection
from ..models import PostElectionResult


class ResultsViewPermissionsMixin(UserPassesTestMixin):
    raise_exception = True
    def test_func(self, user):
        in_group = user_in_group(self.request.user,
            "Trusted to confirm control results")
        results_feature_active = getattr(
            settings, 'RESULTS_FEATURE_ACTIVE', False)

        return any((in_group, results_feature_active))


class BaseResultsViewMixin(ResultsViewPermissionsMixin):

    def get_object(self):
        post_election_id = self.kwargs.get('post_election_id')
        pee = get_object_or_404(
            PostExtraElection,
            pk=post_election_id,
        )
        return PostElectionResult.objects.get_or_create(post_election=pee)[0]
