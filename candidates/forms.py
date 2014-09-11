from .models import MapItData

from django import forms

class PostcodeForm(forms.Form):
    postcode = forms.CharField(
        label='Enter your postcode',
        max_length=20
    )

class ConstituencyForm(forms.Form):
    constituency = forms.ChoiceField(
        label='Select a constituency',
        choices=[('', '')] + sorted(
            [
                (mapit_id, constituency['name'])
                for mapit_id, constituency
                in MapItData.constituencies_2010.items()
            ],
            key=lambda t: t[1]
        )
    )

class CandidacyForm(forms.Form):
    person_id = forms.CharField(
        label='Person ID',
        max_length=256,
    )
    organization_id = forms.CharField(
        label='Candidate List ID',
        max_length=256,
    )

class BasePersonForm(forms.Form):
    name = forms.CharField(
        label="Full name",
        max_length=256,
    )
    party = forms.CharField(
        label="Party",
        max_length=256,
    )
    email = forms.CharField(
        label="Email",
        max_length=256,
        required=False,
    )
    date_of_birth = forms.DateField(
        label="Date of birth",
        required=False,
    )
    wikipedia_url = forms.CharField(
        label="Wikipedia URL",
        max_length=256,
        required=False,
    )
    homepage_url = forms.CharField(
        label="Homepage URL",
        max_length=256,
        required=False,
    )
    twitter_username = forms.CharField(
        label="Twitter username",
        max_length=256,
        required=False,
    )


class NewPersonForm(BasePersonForm):
    organization_id = forms.CharField(
        label="The candidate lists's organization ID",
        max_length=256,
        widget=forms.HiddenInput(),
    )

class UpdatePersonForm(BasePersonForm):
    standing = forms.BooleanField(
        label='Standing in 2015',
        required=False,
    )
    constituency = forms.ChoiceField(
        label='Constituency in 2015',
        required=False,
        choices=[('', '')] + sorted(
            [
                (mapit_id, constituency['name'])
                for mapit_id, constituency
                in MapItData.constituencies_2010.items()
            ],
            key=lambda t: t[1]
        )
    )
