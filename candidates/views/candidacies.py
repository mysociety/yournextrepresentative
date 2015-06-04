from django.views.generic import FormView

from braces.views import LoginRequiredMixin

from auth_helpers.views import user_in_group

from candidates.models import get_area_from_post_id

from .helpers import get_redirect_from_mapit_id
from .version_data import get_client_ip, get_change_metadata
from ..forms import CandidacyCreateForm, CandidacyDeleteForm
from ..models import PopItPerson, LoggedAction, TRUSTED_TO_LOCK_GROUP_NAME
from ..popit import PopItApiMixin
from ..static_data import MapItData

def raise_if_locked(api, request, post_id):
    # If you're a user who's trusted to toggle the constituency lock,
    # they're allowed to edit candidacy:
    if user_in_group(request.user, TRUSTED_TO_LOCK_GROUP_NAME):
        return
    # Otherwise, if the constituency is locked, raise an exception:
    data = api.posts(post_id).get(embed='')
    if data.get('candidates_locked'):
        raise Exception("Attempt to edit a candidacy in a locked constituency")


class CandidacyView(LoginRequiredMixin, PopItApiMixin, FormView):

    form_class = CandidacyCreateForm
    template_name = 'candidates/candidacy-create.html'

    def form_valid(self, form):
        mapit_area_id = form.cleaned_data['mapit_area_id']
        election = self.kwargs['election']
        raise_if_locked(self.api, self.request, mapit_area_id)
        change_metadata = get_change_metadata(
            self.request, form.cleaned_data['source']
        )
        person = PopItPerson.create_from_popit(
            self.api,
            form.cleaned_data['person_id'],
        )
        LoggedAction.objects.create(
            user=self.request.user,
            action_type='candidacy-create',
            ip_address=get_client_ip(self.request),
            popit_person_new_version=change_metadata['version_id'],
            popit_person_id=person.id,
            source=change_metadata['information_source'],
        )
        # Update standing_in and party_memberships:
        new_standing_in = person.standing_in.copy()
        new_standing_in[election] = get_area_from_post_id(
            mapit_area_id,
            mapit_url_key='mapit_url'
        )
        person.standing_in = new_standing_in
        new_party_memberships = person.party_memberships.copy()
        new_party_memberships[election] = person.last_party_reduced
        person.party_memberships = new_party_memberships

        person.record_version(change_metadata)
        person.save_to_popit(self.api)
        person.invalidate_cache_entries()
        return get_redirect_from_mapit_id(election, mapit_area_id)

    def get_context_data(self, **kwargs):
        context = super(CandidacyView, self).get_context_data(**kwargs)
        context['person'], _ = self.get_person(self.request.POST.get('person_id'))
        context['constituency'] = MapItData.areas_by_id[('WMC', 22)].get(
            self.request.POST.get('mapit_area_id')
        )
        return context


class CandidacyDeleteView(LoginRequiredMixin, PopItApiMixin, FormView):

    form_class = CandidacyDeleteForm
    template_name = 'candidates/candidacy-delete.html'

    def form_valid(self, form):
        mapit_area_id = form.cleaned_data['mapit_area_id']
        election = self.kwargs['election']
        raise_if_locked(self.api, self.request, mapit_area_id)
        change_metadata = get_change_metadata(
            self.request, form.cleaned_data['source']
        )
        person = PopItPerson.create_from_popit(
            self.api,
            form.cleaned_data['person_id'],
        )
        LoggedAction.objects.create(
            user=self.request.user,
            action_type='candidacy-delete',
            ip_address=get_client_ip(self.request),
            popit_person_new_version=change_metadata['version_id'],
            popit_person_id=person.id,
            source=change_metadata['information_source'],
        )

        # Update standing_in and party_memberships:
        new_standing_in = deepcopy(person.standing_in)
        new_standing_in[election] = None
        person.standing_in = new_standing_in
        new_party_memberships = deepcopy(person.party_memberships)
        new_party_memberships.pop(election, None)
        person.party_memberships = new_party_memberships

        person.record_version(change_metadata)
        person.save_to_popit(self.api)
        person.invalidate_cache_entries()
        return get_redirect_from_mapit_id(election, mapit_area_id)

    def get_context_data(self, **kwargs):
        context = super(CandidacyDeleteView, self).get_context_data(**kwargs)
        context['person'], _ = self.get_person(self.request.POST.get('person_id'))
        context['constituency'] = MapItData.areas_by_id[('WMC', 22)].get(
            self.request.POST.get('mapit_area_id')
        )
        return context
