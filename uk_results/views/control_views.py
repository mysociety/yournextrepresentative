from django.views.generic import (TemplateView, DetailView, FormView,
                                  ListView, UpdateView)

from ..constants import CONFIRMED_STATUS
from ..models import CouncilElection, CouncilElectionResultSet
from ..forms import (ReportCouncilElectionControlForm,
                     ReviewControlForm)
from .base import BaseResultsViewMixin


class CouncilsWithElections(BaseResultsViewMixin, TemplateView):
    template_name = "uk_results/councils_with_elections.html"

    def get_context_data(self, **kwargs):
        context = super(CouncilsWithElections, self).get_context_data(**kwargs)
        councils = CouncilElection.objects.all().order_by('council__name')
        councils = councils.select_related('council', 'election')
        context['council_elections'] = councils

        return context


class CouncilElectionView(BaseResultsViewMixin, DetailView):
    model = CouncilElection

    def get_object(self):
        gss = self.kwargs.get('gss')
        council_election = CouncilElection.objects.get(council__council_id=gss)
        return council_election



class ReportCouncilElectionView(BaseResultsViewMixin, FormView):
    model = CouncilElection
    pk_url_kwarg = 'council_election'
    template_name = "uk_results/report_council_election_control.html"

    def get_context_data(self, **kwargs):
        context = super(ReportCouncilElectionView, self).get_context_data(**kwargs)
        context['object'] = self.object
        return context

    def get_form(self, form_class=None):
        """
        Returns an instance of the form to be used in this view.
        """
        self.object = self.model.objects.get(
            pk=self.kwargs['council_election']
        )

        return ReportCouncilElectionControlForm(
            council_election=self.object,
            **self.get_form_kwargs()
        )

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        instance = form.save()
        if 'report_and_confirm' in self.request.POST:
            instance.review_status = CONFIRMED_STATUS
            instance.save()
        return super(ReportCouncilElectionView, self).form_valid(form)


class LatestControlResults(BaseResultsViewMixin, ListView):
    template_name = "uk_results/latest_control_results.html"
    queryset = CouncilElectionResultSet.objects.all()

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


class ConfirmControl(BaseResultsViewMixin, UpdateView):
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
