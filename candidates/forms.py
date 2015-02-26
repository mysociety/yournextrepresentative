import re

from .static_data import MapItData, PartyData

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from .mapit import get_wmc_from_postcode, BaseMapItException

class PostcodeForm(forms.Form):
    postcode = forms.CharField(
        label='Enter your postcode',
        max_length=20
    )

    def clean_postcode(self):
        postcode = self.cleaned_data['postcode']
        try:
            # Go to MapIt to check if this postcode is valid and
            # contained in a constituency. (If it's valid then the
            # result is cached, so this doesn't cause a double lookup.)
            get_wmc_from_postcode(postcode)
        except BaseMapItException as e:
            raise ValidationError(unicode(e))
        return postcode

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

    def clean_constituency(self):
        constituency = self.cleaned_data['constituency']
        if constituency == 'none':
            raise ValidationError("You must select a constituency")
        return constituency

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
        label=u"Source of information that they're standing ({0})".format(
            settings.SOURCE_HINTS
        ),
        max_length=512,
    )

class CandidacyDeleteForm(BaseCandidacyForm):
    source = forms.CharField(
        label=u"Information source for this change ({0})".format(
            settings.SOURCE_HINTS
        ),
        max_length=512,
    )

class BasePersonForm(forms.Form):
    honorific_prefix = forms.CharField(
        label="Title / pre-nominal honorific (e.g. Dr, Sir, etc.)",
        max_length=64,
        required=False,
    )
    name = forms.CharField(
        label="Full name",
        max_length=256,
    )
    honorific_suffix = forms.CharField(
        label="Post-nominal letters (e.g. CBE, DSO, etc.)",
        max_length=64,
        required=False,
    )
    email = forms.EmailField(
        label="Email",
        max_length=256,
        required=False,
    )
    gender = forms.CharField(
        label="Gender (e.g. \"male\", \"female\")",
        max_length=256,
        required=False,
    )
    birth_date = forms.DateField(
        label="Date of birth (as YYYY-MM-DD)",
        required=False,
    )
    wikipedia_url = forms.URLField(
        label="Wikipedia URL",
        max_length=256,
        required=False,
    )
    homepage_url = forms.URLField(
        label="Homepage URL",
        max_length=256,
        required=False,
    )
    twitter_username = forms.CharField(
        label="Twitter username (e.g. \"democlub\")",
        max_length=256,
        required=False,
    )
    facebook_personal_url = forms.URLField(
        label="Facebook profile URL",
        max_length=256,
        required=False,
    )
    facebook_page_url = forms.URLField(
        label="Facebook page (e.g. for their campaign)",
        max_length=256,
        required=False,
    )
    linkedin_url = forms.URLField(
        label="LinkedIn URL",
        max_length=256,
        required=False,
    )
    party_ppc_page_url = forms.URLField(
        label="The party's PPC page for this person",
        max_length=256,
        required=False,
    )

    def clean_twitter_username(self):
        # Remove any URL bits around it:
        username = self.cleaned_data['twitter_username'].strip()
        m = re.search('^.*twitter.com/(\w+)', username)
        if m:
            username = m.group(1)
        # If there's a leading '@', strip that off:
        username = re.sub(r'^@', '', username)
        if not re.search(r'^\w*$', username):
            message = "The Twitter username must only consist of alphanumeric characters or underscore"
            raise ValidationError(message)
        return username

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
        label=u"Source of information ({0})".format(
            settings.SOURCE_HINTS
        ),
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
    STANDING_CHOICES = (
        ('not-sure', "Don't Know"),
        ('standing', "Yes"),
        ('not-standing', "No"),
    )
    standing = forms.ChoiceField(
        label='Standing in 2015',
        choices=STANDING_CHOICES,
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
        label=u"Source of information for this change ({0})".format(
            settings.SOURCE_HINTS
        ),
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
        if cleaned_data['standing'] == 'standing':
            return self.check_party_and_constituency_are_selected(cleaned_data)
        return cleaned_data
