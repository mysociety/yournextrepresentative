from django.db.models import Prefetch
from django.views.generic import (TemplateView, DetailView, FormView,
                                  ListView, UpdateView)

from candidates.views.version_data import get_client_ip
from candidates.models import LoggedAction
from elections.models import Election

from ..constants import CONFIRMED_STATUS, RESULTS_DATE
from ..models import CouncilElection, CouncilElectionResultSet
from ..forms import (ReportCouncilElectionControlForm,
                     ReviewControlForm)
from .base import BaseResultsViewMixin, ResultsViewPermissionsMixin


class CouncilsWithElections(BaseResultsViewMixin, TemplateView):
    template_name = "uk_results/councils_with_elections.html"

    def get_context_data(self, **kwargs):
        context = super(CouncilsWithElections, self).get_context_data(**kwargs)
        councils = CouncilElection.objects.all().order_by(
            '-election__election_date', 'council__name')
        councils = councils.select_related(
            'council',
            'election',
            'controller_resultset',
            'controller_resultset__controller',
            'controller_resultset__controller__partywithcolour',
            # 'reported_results',
        )
        councils = councils.prefetch_related(
            Prefetch(
                'reported_results',
                CouncilElectionResultSet.objects.select_related(
                    'council_election',
                    'council_election__election',
                    'council_election__council',
                    'council_election__council',
                )
            )
        )
        context['council_elections'] = councils

        return context


class CouncilElectionView(BaseResultsViewMixin, DetailView):
    model = CouncilElection

    def get_object(self):
        election_id = self.kwargs.get('election_id')
        council_election = CouncilElection.objects.select_related(
            'election',
            'council',
        )
        council_election = council_election.get(election__slug=election_id)
        return council_election

    def get_context_data(self, **kwargs):
        context = super(CouncilElectionView, self).get_context_data(**kwargs)
        context['post_elections'] = \
            self.object.election.postextraelection_set.all().select_related(
                'postextra__base', 'election'
            )
        return context


class ReportCouncilElectionView(BaseResultsViewMixin, FormView):
    model = CouncilElection
    pk_url_kwarg = 'council_election'
    template_name = "uk_results/report_council_election_control.html"

    def get_context_data(self, **kwargs):
        context = super(
            ReportCouncilElectionView, self).get_context_data(**kwargs)
        context['object'] = self.object
        return context

    def get_form(self, form_class=None):
        """
        Returns an instance of the form to be used in this view.
        """
        self.object = self.model.objects.get(
            election__slug=self.kwargs['election_id']
        )

        return ReportCouncilElectionControlForm(
            council_election=self.object,
            **self.get_form_kwargs()
        )

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        instance = form.save()
        user = None
        if self.request.user.is_authenticated():
            user = self.request.user
            LoggedAction.objects.create(
                user=user,
                action_type='record-council-control',
                ip_address=get_client_ip(self.request),
                source=form['source'].value()
            )
        if 'report_and_confirm' in self.request.POST:
            instance.review_status = CONFIRMED_STATUS
            instance.reviewed_by = self.request.user
            instance.save()

            LoggedAction.objects.create(
                user=self.request.user,
                action_type='confirm-council-control',
                ip_address=get_client_ip(self.request),
                source="Confirmed when reporting",
            )

        return super(ReportCouncilElectionView, self).form_valid(form)


class LatestControlResults(BaseResultsViewMixin, ListView):
    template_name = "uk_results/latest_control_results.html"
    queryset = CouncilElectionResultSet.objects.all()

    def get_queryset(self):
        queryset = self.queryset
        queryset = queryset.filter(
            council_election__election__election_date=RESULTS_DATE)
        queryset = queryset.select_related(
            'controller', 'council_election__council')

        status = self.request.GET.get('status')
        if status:
            if status == "confirmed":
                queryset = queryset.confirmed()
            if status == "unconfirmed":
                queryset = queryset.unconfirmed()
            if status == "rejected":
                queryset = queryset.rejected()
        return queryset


class ConfirmControl(ResultsViewPermissionsMixin, UpdateView):
    template_name = "uk_results/review_reported_control.html"
    queryset = CouncilElectionResultSet.objects.all()

    def get_form(self, form_class=None):
        kwargs = self.get_form_kwargs()
        kwargs['initial'].update({'reviewed_by': self.request.user})
        return ReviewControlForm(
            **kwargs
        )

    def get_success_url(self):
        return self.object.council_election.get_absolute_url()

    def form_valid(self, form):
        form.save()
        LoggedAction.objects.create(
            user=self.request.user,
            action_type='confirm-council-control',
            ip_address=get_client_ip(self.request),
            source=form['review_source'].value()
        )
        return super(ConfirmControl, self).form_valid(form)
