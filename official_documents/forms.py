from django import forms

from .models import OfficialDocument

class UploadDocumentForm(forms.ModelForm):
    class Meta:
        model = OfficialDocument
        fields = (
            'uploaded_file',
            'source_url',
            'mapit_id'
        )

    mapit_id = forms.CharField(widget=forms.HiddenInput())
