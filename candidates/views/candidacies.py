from django.views.generic import FormView

from braces.views import LoginRequiredMixin

from .helpers import get_redirect_from_mapit_id
from .mixins import CandidacyMixin
from .version_data import get_client_ip
from ..forms import CandidacyCreateForm, CandidacyDeleteForm
from ..models import LoggedAction
from ..static_data import MapItData
from ..update import PersonParseMixin, PersonUpdateMixin


class CandidacyView(LoginRequiredMixin, CandidacyMixin, PersonParseMixin, PersonUpdateMixin, FormView):

    form_class = CandidacyCreateForm
    template_name = 'candidates/candidacy-create.html'

    def form_valid(self, form):
        change_metadata = self.get_change_metadata(
            self.request, form.cleaned_data['source']
        )
        LoggedAction.objects.create(
            user=self.request.user,
            action_type='candidacy-create',
            ip_address=get_client_ip(self.request),
            popit_person_new_version=change_metadata['version_id'],
            popit_person_id=form.cleaned_data['person_id'],
            source=change_metadata['information_source'],
        )
        our_person, _ = self.get_person(form.cleaned_data['person_id'])
        previous_versions = our_person.pop('versions')

        our_person['standing_in']['2015'] = self.get_area_from_post_id(
            form.cleaned_data['mapit_area_id'],
            mapit_url_key='mapit_url'
        )
        our_person['party_memberships']['2015'] = our_person['party_memberships']['2010']

        self.update_person(our_person, change_metadata, previous_versions)
        return get_redirect_from_mapit_id(form.cleaned_data['mapit_area_id'])

    def get_context_data(self, **kwargs):
        context = super(CandidacyView, self).get_context_data(**kwargs)
        context['person'], _ = self.get_person(self.request.POST.get('person_id'))
        context['constituency'] = MapItData.constituencies_2010.get(
            self.request.POST.get('mapit_area_id')
        )
        return context


class CandidacyDeleteView(LoginRequiredMixin, CandidacyMixin, PersonParseMixin, PersonUpdateMixin, FormView):

    form_class = CandidacyDeleteForm
    template_name = 'candidates/candidacy-delete.html'

    def form_valid(self, form):
        change_metadata = self.get_change_metadata(
            self.request, form.cleaned_data['source']
        )
        LoggedAction.objects.create(
            user=self.request.user,
            action_type='candidacy-delete',
            ip_address=get_client_ip(self.request),
            popit_person_new_version=change_metadata['version_id'],
            popit_person_id=form.cleaned_data['person_id'],
            source=change_metadata['information_source'],
        )
        our_person, _ = self.get_person(form.cleaned_data['person_id'])
        previous_versions = our_person.pop('versions')

        our_person['standing_in']['2015'] = None
        our_person['party_memberships'].pop('2015', None)

        self.update_person(our_person, change_metadata, previous_versions)
        return get_redirect_from_mapit_id(form.cleaned_data['mapit_area_id'])

    def get_context_data(self, **kwargs):
        context = super(CandidacyDeleteView, self).get_context_data(**kwargs)
        context['person'], _ = self.get_person(self.request.POST.get('person_id'))
        context['constituency'] = MapItData.constituencies_2010.get(
            self.request.POST.get('mapit_area_id')
        )
        return context
