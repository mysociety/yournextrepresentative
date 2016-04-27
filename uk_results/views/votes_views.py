from django.views.generic import (DetailView, FormView, UpdateView, ListView)

from popolo.models import Post
from ..models import PostResult, ResultSet
from ..forms import ResultSetForm, ReviewVotesForm
from .base import BaseResultsViewMixin


class PostResultsView(BaseResultsViewMixin, DetailView):
    template_name = "uk_results/posts/post_view.html"

    def get_object(self):
        slug = self.kwargs.get('post_id')
        post = Post.objects.get(extra__slug=slug)
        return PostResult.objects.get_or_create(post=post)[0]



class PostReportVotesView(BaseResultsViewMixin, FormView):
    model = PostResult
    template_name = "uk_results/report_council_election_control.html"

    def get_object(self):
        slug = self.kwargs.get('post_id')
        post = Post.objects.get(extra__slug=slug)
        return PostResult.objects.get_or_create(post=post)[0]

    def get_context_data(self, **kwargs):
        context = super(PostReportVotesView, self).get_context_data(**kwargs)
        context['object'] = self.object
        return context

    def get_form(self, form_class=None):
        """
        Returns an instance of the form to be used in this view.
        """
        self.object = self.get_object()

        return ResultSetForm(
            post_result=self.object,
            **self.get_form_kwargs()
        )

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        form.save(self.request)
        return super(PostReportVotesView, self).form_valid(form)




class ReviewPostReportView(BaseResultsViewMixin, UpdateView):
    template_name = "uk_results/posts/review_reported_votes.html"
    queryset = ResultSet.objects.all()

    def get_form(self, form_class=None):
        kwargs = self.get_form_kwargs()
        kwargs['initial'].update({'reviewed_by': self.request.user})
        return ReviewVotesForm(
            **kwargs
        )

    def get_success_url(self):
        return self.object.post_result.get_absolute_url()



class LatestVoteResults(BaseResultsViewMixin, ListView):
    template_name = "uk_results/posts/latest_vote_results.html"
    queryset = ResultSet.objects.all()

    def get_queryset(self):
        queryset = self.queryset
        status = self.request.GET.get('status')
        if status:
            if status == "confirmed":
                queryset = queryset.confirmed()
            if status == "unconfirmed":
                queryset = queryset.unconfirmed()
            if status == "rejected":
                queryset = queryset.rejected()
        return queryset
