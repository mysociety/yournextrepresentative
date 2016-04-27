from django.conf import settings

from braces.views import UserPassesTestMixin

from auth_helpers.views import user_in_group


class BaseResultsViewMixin(UserPassesTestMixin):
    raise_exception = True
    def test_func(self, user):
        in_group = user_in_group(self.request.user,
            "Trusted to confirm control results")
        results_feature_active = getattr(
            settings, 'RESULTS_FEATURE_ACTIVE', False)

        return any(
                (in_group, results_feature_active)
            )



