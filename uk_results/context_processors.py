from django.conf import settings

def show_results_feature(request):
    in_group = request.user.groups.filter(
        name='Trusted to confirm control results').exists()
    results_feature_active = getattr(settings, 'RESULTS_FEATURE_ACTIVE', False)

    return {
        'show_results_feature': any(
            (in_group, results_feature_active)
        ),
    }

