from django.views.generic import (TemplateView, DetailView, FormView,
                                  ListView, UpdateView)

from ..models import CouncilElection, CouncilElectionResultSet
from ..forms import (ReportCouncilElectionControlForm,
                     ReviewControlForm)


class CouncilsWithElections(TemplateView):
    template_name = "uk_results/councils_with_elections.html"

    def get_context_data(self, **kwargs):
        context = super(CouncilsWithElections, self).get_context_data(**kwargs)
        councils = CouncilElection.objects.all().order_by('council__name')
        councils = councils.select_related('council', 'election')
        context['council_elections'] = councils

        return context


class CouncilElectionView(DetailView):
    model = CouncilElection


class ReportCouncilElectionView(FormView):
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
        form.save()
        return super(ReportCouncilElectionView, self).form_valid(form)


class LatestControlResults(ListView):
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


class ConfirmControl(UpdateView):
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
