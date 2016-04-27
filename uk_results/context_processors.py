from django.conf import settings

from auth_helpers.views import user_in_group

def show_results_feature(request):
    in_group = user_in_group(request.user,
        "Trusted to confirm control results")
    results_feature_active = getattr(settings, 'RESULTS_FEATURE_ACTIVE', False)

    return {
        'show_results_feature': any(
            (in_group, results_feature_active)
        ),
    }

