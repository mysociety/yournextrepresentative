from django import forms

class PostcodeForm(forms.Form):
    postcode = forms.CharField(
        label='Postcode',
        max_length=20
    )

class CandidacyForm(forms.Form):
    person_id = forms.CharField(
        label='Person ID',
        max_length=256,
    )
    candidate_list_id = forms.CharField(
        label='Candidate List ID',
        max_length=256,
    )
