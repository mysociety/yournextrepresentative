from .static_data import MapItData, PartyData

from django import forms

class PostcodeForm(forms.Form):
    postcode = forms.CharField(
        label='Enter your postcode',
        max_length=20
    )

class ConstituencyForm(forms.Form):
    constituency = forms.ChoiceField(
        label='Select a constituency',
        choices=[('none', '')] + sorted(
            [
                (mapit_id, constituency['name'])
                for mapit_id, constituency
                in MapItData.constituencies_2010.items()
            ],
            key=lambda t: t[1]
        )
    )


class BaseCandidacyForm(forms.Form):
    person_id = forms.CharField(
        label='Person ID',
        max_length=256,
    )
    mapit_area_id = forms.CharField(
        label='MapIt Area ID',
        max_length=256,
    )

class CandidacyCreateForm(BaseCandidacyForm):
    source = forms.CharField(
        label="Source of information that they're standing",
        max_length=512,
    )

class CandidacyDeleteForm(BaseCandidacyForm):
    source = forms.CharField(
        label="Information source for this change",
        max_length=512,
    )

class BasePersonForm(forms.Form):
    name = forms.CharField(
        label="Full name",
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
    facebook_personal_url = forms.CharField(
        label="Facebook profile URL",
        max_length=256,
        required=False,
    )
    facebook_page_url = forms.CharField(
        label="Facebook page (e.g. for their campaign)",
        max_length=256,
        required=False,
    )
    party_ppc_page_url = forms.CharField(
        label="The party's PPC page for this person",
        max_length=256,
        required=False,
    )

    def check_party_and_constituency_are_selected(self, cleaned_data):
        '''This is called by the clean method of subclasses'''

        # Make sure that there is a party selected; we need to do this
        # from the clean method rather than single field validation
        # since the party field that should be checked depends on the
        # selected constituency.
        constituency = cleaned_data['constituency']
        try:
            mapit_area = MapItData.constituencies_2010[constituency]
        except KeyError:
            message = "If you mark the candidate as standing in 2015, you must select a constituency"
            raise forms.ValidationError(message)
        if mapit_area['country_name'] == 'Northern Ireland':
            party_field = 'party_ni'
        else:
            party_field = 'party_gb'
        party_id = cleaned_data[party_field]
        if party_id not in PartyData.party_id_to_name:
            message = "You must specify a party for the 2015 election"
            raise forms.ValidationError(message)
        return cleaned_data


class NewPersonForm(BasePersonForm):
    constituency = forms.CharField(
        label="Constituency in 2015",
        max_length=256,
        widget=forms.HiddenInput(),
    )
    gender = forms.CharField(
        label="Gender (e.g. 'male', 'female')",
        max_length=256,
        required=False,
    )
    party_gb = forms.ChoiceField(
        label="Party in 2015 (Great Britain)",
        choices=PartyData.party_choices['Great Britain'],
        required=False,
    )
    party_ni = forms.ChoiceField(
        label="Party in 2015 (Northern Ireland)",
        choices=PartyData.party_choices['Northern Ireland'],
        required=False,
    )
    source = forms.CharField(
        label="Source of information",
        max_length=512,
        error_messages={
            'required': 'You must indicate how you know about this candidate'
        },
        widget=forms.TextInput(
            attrs={
                'required': 'required',
                'placeholder': 'How you know about this candidate'
            }
        )
    )

    def clean(self):
        cleaned_data = super(NewPersonForm, self).clean()
        return self.check_party_and_constituency_are_selected(cleaned_data)

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
    party_gb = forms.ChoiceField(
        label="Party in 2015 (Great Britain)",
        choices=PartyData.party_choices['Great Britain'],
        required=False,
    )
    party_ni = forms.ChoiceField(
        label="Party in 2015 (Northern Ireland)",
        choices=PartyData.party_choices['Northern Ireland'],
        required=False,
    )
    source = forms.CharField(
        label="Source of information for this change",
        max_length=512,
        error_messages={
            'required': 'You must indicate how you know about this candidate'
        },
        widget=forms.TextInput(
            attrs={
                'required': 'required',
                'placeholder': 'How you know about this candidate'
            }
        )
    )

    def clean(self):
        cleaned_data = super(UpdatePersonForm, self).clean()
        if cleaned_data['standing']:
            return self.check_party_and_constituency_are_selected(cleaned_data)
        return cleaned_data
