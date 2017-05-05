from django.shortcuts import get_object_or_404
from django.utils.six.moves.urllib_parse import urlencode

from django.views.generic import (DetailView, FormView, UpdateView, ListView)

from candidates.views.version_data import get_client_ip
from candidates.models import LoggedAction

from popolo.models import Post

from ..constants import CONFIRMED_STATUS, RESULTS_DATE
from ..models import PostResult, ResultSet
from ..forms import ResultSetForm, ReviewVotesForm
from .base import BaseResultsViewMixin


class PostResultsView(BaseResultsViewMixin, DetailView):
    template_name = "uk_results/posts/post_view.html"

    def get_object(self):
        slug = self.kwargs.get('post_id')
        post = get_object_or_404(Post, extra__slug=slug)
        return PostResult.objects.get_or_create(post=post)[0]


class PostReportVotesView(BaseResultsViewMixin, FormView):
    model = PostResult
    template_name = "uk_results/report_council_election_control.html"

    def get_object(self):
        slug = self.kwargs.get('post_id')
        post = get_object_or_404(Post, extra__slug=slug)
        return PostResult.objects.get_or_create(post=post)[0]

    def get_context_data(self, **kwargs):
        context = super(PostReportVotesView, self).get_context_data(**kwargs)
        context['object'] = self.object
        return context

    def get_form_kwargs(self):
        kwargs = super(PostReportVotesView, self).get_form_kwargs()
        for k, v in self.request.GET.items():
            new_k = "initial-{}".format(k)
            kwargs[new_k] = v
        return kwargs

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
        instance = form.save(self.request)
        user = None
        if self.request.user.is_authenticated():
            user = self.request.user
            LoggedAction.objects.create(
                user=user,
                action_type='record-council-result',
                ip_address=get_client_ip(self.request),
                source=form['source'].value(),
                post=form.post,
            )

        if 'report_and_confirm' in self.request.POST:
            instance.review_status = CONFIRMED_STATUS
            instance.save()
            if self.request.user.is_authenticated():
                user = self.request.user
                LoggedAction.objects.create(
                    user=user,
                    action_type='confirm-council-result',
                    ip_address=get_client_ip(self.request),
                    source="Confirmed when reporting",
                    post=form.post,
                )

        return super(PostReportVotesView, self).form_valid(form)


class ReviewPostReportView(BaseResultsViewMixin, UpdateView):
    template_name = "uk_results/posts/review_reported_votes.html"
    queryset = ResultSet.objects.all()

    def get_form(self, form_class=None):
        kwargs = self.get_form_kwargs()
        kwargs['initial'].update({'reviewed_by': self.request.user})
        return ReviewVotesForm(
            self.request,
            review_result=self.object,
            **kwargs
        )

    def get_success_url(self):
        return self.object.post_result.get_absolute_url()

    def get_edit_url(self):
        data = {
            'source': self.object.source,
            'num_turnout_reported': self.object.num_turnout_reported,
            'num_spoilt_ballots': self.object.num_spoilt_ballots,
        }
        for result in self.object.candidate_results.all():
            data['memberships_{}'.format(result.membership.person.pk)] = result.num_ballots_reported
        return urlencode(data)

    def get_context_data(self, **kwargs):
        context = super(ReviewPostReportView, self).get_context_data(**kwargs)
        context['edit_querystring'] = self.get_edit_url()
        return context


    def form_valid(self, form):
        form.save()
        if self.request.user.is_authenticated():
            user = self.request.user
            LoggedAction.objects.create(
                user=user,
                action_type='confirm-council-result',
                ip_address=get_client_ip(self.request),
                source=form['review_source'].value(),
                post=form.post,
            )
        return super(ReviewPostReportView, self).form_valid(form)


class LatestVoteResults(BaseResultsViewMixin, ListView):
    template_name = "uk_results/posts/latest_vote_results.html"
    queryset = ResultSet.objects.all()
    paginate_by = 30

    def get_queryset(self):
        queryset = super(LatestVoteResults, self).get_queryset()
        queryset = queryset.filter(
            post_result__post__extra__elections__election_date=RESULTS_DATE)
        queryset = queryset.select_related('post_result',)
        queryset = queryset.select_related('post_result__post',)
        queryset = queryset.select_related('post_result__post__area',)
        queryset = queryset.prefetch_related(
            'candidate_results__membership__person',)
        queryset = queryset.prefetch_related(
            'candidate_results__membership__on_behalf_of__partywithcolour',)


        status = self.request.GET.get('status')
        if status:
            if status == "confirmed":
                queryset = queryset.confirmed()
            if status == "unconfirmed":
                queryset = queryset.unconfirmed()
                queryset = queryset.filter(
                    post_result__confirmed_resultset=None)
            if status == "rejected":
                queryset = queryset.rejected()
        queryset = queryset.order_by(
            'post_result__post__extra__postextraelection__election')
        return queryset
