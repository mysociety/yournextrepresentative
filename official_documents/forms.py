from django import forms

from .models import OfficialDocument

class UploadDocumentForm(forms.ModelForm):
    class Meta:
        model = OfficialDocument
        fields = (
            'election',
            'uploaded_file',
            'source_url',
            'post',
            'document_type',
        )

        widgets = {'post': forms.HiddenInput()}

    election = forms.CharField(widget=forms.HiddenInput())
    document_type = forms.CharField(widget=forms.HiddenInput())
