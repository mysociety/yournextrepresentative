import re

from django import forms
from django.core.exceptions import ValidationError

from .models import QueuedImage

class UploadPersonPhotoForm(forms.ModelForm):

    class Meta:
        model = QueuedImage
        fields = [
            'image', 'public_domain', 'use_allowed_by_owner',
            'justification_for_use', 'popit_person_id', 'decision'
        ]
        widgets = {
            'popit_person_id': forms.HiddenInput(),
            'decision': forms.HiddenInput(),
            'justification_for_use': forms.Textarea(
                attrs={'rows': 1, 'columns': 72}
            )
        }

    def clean_popit_person_id(self):
        popit_person_id = self.cleaned_data['popit_person_id']
        if not re.search(r'^\d+$', popit_person_id):
            raise ValidationError("The popit_person_id must be all digits")
        return popit_person_id

    def clean(self):
        cleaned_data = super(UploadPersonPhotoForm, self).clean()
        public_domain = cleaned_data.get('public_domain')
        use_allowed_by_owner = cleaned_data.get('use_allowed_by_owner')
        definitely_allowed = public_domain or use_allowed_by_owner
        justification_for_use = cleaned_data.get('justification_for_use', '').strip()
        if not (justification_for_use or definitely_allowed):
            message = "If the photo isn't public domain or owned by you, " + \
                "then you must provide a justification for why we can use it."
            raise ValidationError(message)
        return cleaned_data


class PhotoReviewForm(forms.Form):

    queued_image_id = forms.IntegerField(
        required=True,
        widget=forms.HiddenInput(),
    )
    x_min = forms.IntegerField(min_value=0)
    x_max = forms.IntegerField(min_value=1)
    y_min = forms.IntegerField(min_value=0)
    y_max = forms.IntegerField(min_value=1)
    decision = forms.ChoiceField(choices=QueuedImage.DECISION_CHOICES)
    rejection_reason = forms.CharField(
        widget=forms.Textarea(),
        required=False
    )
    justification_for_use = forms.CharField(
        widget=forms.Textarea(),
        required=False
    )
