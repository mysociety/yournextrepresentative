from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView

from candidates.popit import create_popit_api_object
from candidates.models import PopItPerson

from .forms import UploadPersonPhotoForm

def upload_photo(request, popit_person_id):
    if request.method == 'POST':
        form = UploadPersonPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            # Make sure that we save the user that made the upload
            queued_image = form.save(commit=False)
            queued_image.user = request.user
            queued_image.save()
            return HttpResponseRedirect(reverse(
                'photo-upload-success',
                kwargs={
                    'popit_person_id': form.cleaned_data['popit_person_id']
                }
            ))
    else:
        form = UploadPersonPhotoForm(
            initial={
                'popit_person_id': popit_person_id
            }
        )
    api = create_popit_api_object()
    return render(
        request,
        'moderation_queue/photo-upload-new.html',
        {'form': form,
         'person': PopItPerson.create_from_popit(api, popit_person_id)}
    )


class PhotoUploadSuccess(PersonParseMixin, TemplateView):
    template_name = 'moderation_queue/photo-upload-success.html'

    def get_context_data(self, **kwargs):
        context = super(PhotoUploadSuccess, self).get_context_data(**kwargs)
        context['person'], _ = self.get_person(kwargs['popit_person_id'])
        return context
