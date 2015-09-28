from django.conf import settings
from django.views.generic import TemplateView

from ..cache import get_all_posts_cached
from ..popit import PopItApiMixin
from elections.models import Election

class PostListView(PopItApiMixin, TemplateView):
    template_name = 'candidates/posts.html'

    def get_context_data(self, **kwargs):
        context = super(PostListView, self).get_context_data(**kwargs)

        all_posts = {}
        for election_data in Election.objects.current().by_date():
            role = election_data.for_post_role
            all_posts[election_data.slug] = {
                'posts': get_all_posts_cached(self.api, election_data.slug, role),
                'election_data': election_data,
            }
        context['all_posts'] = all_posts
        return context
