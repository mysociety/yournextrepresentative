from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView

from slugify import slugify

from popolo.models import Post
from candidates.views.mixins import ContributorsMixin
from .forms import ConstituencySelectorForm


class ConstituencySelectorView(ContributorsMixin, FormView):

    template_name = 'jamaica/frontpage.html'
    form_class = ConstituencySelectorForm

    @method_decorator(cache_control(max_age=(60 * 10)))
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super(ConstituencySelectorView, self).dispatch(*args, **kwargs)

    """
    We know there is only one election and one post for each area so
    hard code those assumptions to reduce clicks
    """
    def form_valid(self, form):
        area = form.cleaned_data['cons_area_id']
        post = Post.objects.filter(area=area) \
            .select_related('extra') \
            .prefetch_related('extra__elections') \
            .first()
        return HttpResponseRedirect(
            reverse('constituency', kwargs={
                'election': post.extra.elections.first().slug,
                'post_id': post.extra.slug,
                'ignored_slug': slugify(post.label)
            })
        )

    def get_context_data(self, **kwargs):
        context = super(ConstituencySelectorView, self).get_context_data(**kwargs)
        context['top_users'] = self.get_leaderboards()[1]['rows'][:8]
        context['recent_actions'] = self.get_recent_changes_queryset()[:5]
        return context
