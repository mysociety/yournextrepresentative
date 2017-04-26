from __future__ import unicode_literals

from django.views.generic import TemplateView

from elections.models import Election

class PostListView(TemplateView):
    template_name = 'candidates/posts.html'

    def get_context_data(self, **kwargs):
        context = super(PostListView, self).get_context_data(**kwargs)
        context['elections_and_posts'] = \
            Election.group_and_order_elections(
                include_postextraelections=True, include_noncurrent=False)
        return context
