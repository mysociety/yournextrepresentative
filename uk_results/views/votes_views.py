from django.utils.six.moves.urllib_parse import urlencode
from django.http import Http404
from django.core.urlresolvers import reverse

from django.views.generic import (
    DetailView, FormView, UpdateView, ListView, RedirectView)

from candidates.views.version_data import get_client_ip
from candidates.models import LoggedAction, PostExtraElection

from ..constants import CONFIRMED_STATUS, RESULTS_DATE
from ..models import PostElectionResult, ResultSet
from ..forms import ResultSetForm, ReviewVotesForm
from .base import BaseResultsViewMixin, ResultsViewPermissionsMixin


class PostResultsView(BaseResultsViewMixin, DetailView):
    template_name = "uk_results/posts/post_view.html"


class PostReportVotesView(BaseResultsViewMixin, FormView):
    model = PostElectionResult
    template_name = "uk_results/report_council_election_control.html"

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
            post_election_result=self.object,
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
                post=form.post_election.postextra.base,
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
                    post=form.post_election.postextra.base,
                )

        return super(PostReportVotesView, self).form_valid(form)


class ReviewPostReportView(ResultsViewPermissionsMixin, UpdateView):
    template_name = "uk_results/posts/review_reported_votes.html"
    queryset = ResultSet.objects.all().select_related(
        'post_election_result',
    ).prefetch_related(
        'candidate_results__membership',
        'candidate_results__membership__on_behalf_of__partywithcolour',
        'candidate_results__membership__person',
    )
    pk_url_kwarg = 'result_set_id'

    def get_form(self, form_class=None):
        kwargs = self.get_form_kwargs()
        kwargs['initial'].update({'reviewed_by': self.request.user})
        return ReviewVotesForm(
            self.request,
            review_result=self.object,
            **kwargs
        )

    def get_success_url(self):
        return self.object.post_election_result.get_absolute_url()

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
                post=form.post_election.post_election.postextra.base,
            )
        return super(ReviewPostReportView, self).form_valid(form)


class LatestVoteResults(BaseResultsViewMixin, ListView):
    template_name = "uk_results/posts/latest_vote_results.html"
    queryset = ResultSet.objects.all()
    paginate_by = 30

    def get_queryset(self):
        queryset = super(LatestVoteResults, self).get_queryset()
        queryset = queryset.filter(
            post_election_result__post_election__election__election_date=RESULTS_DATE)
        queryset = queryset.select_related(
            'post_election_result',
            'post_election_result__post_election',
            'post_election_result__post_election__postextra',
        )
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
                    post_election_result__confirmed_resultset=None)
            if status == "rejected":
                queryset = queryset.rejected()
        queryset = queryset.order_by(
            'post_election_result__post_election__election')
        return queryset


class PostResultsRedirectView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        """
        For historic reasons there are public URLs that only contain
        a single PostExtra slug rather than an identifier for a
        PostExtraElection.

        To make these URLs continue to work, we redirect form them to
        the newer style URLs.

        This is a "better than nothing" guess. Because the URLs are old, we
        assume the oldest PostExtraElection is the desired one.
        """

        pee = PostExtraElection.objects.filter(
            postextra__slug=kwargs['post_slug']
        ).order_by('election__election_date').first()
        if not pee:
            raise Http404("No post with that ID found")
        return reverse('post-results-view', kwargs={
            'post_election_id': pee.pk})
