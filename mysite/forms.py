from __future__ import unicode_literals

from django import forms

from allauth.account.forms import LoginForm, SignupForm

from django.utils.translation import ugettext_lazy as _


class CustomLoginForm(LoginForm):

    def __init__(self, *args, **kwargs):
        super(CustomLoginForm, self).__init__(*args, **kwargs)
        self.fields['login'].label = _('Username or email address')
        # Remove the placeholder text, which just adds noise:
        for field in ('login', 'password'):
            del self.fields[field].widget.attrs['placeholder']


class CustomSignupForm(SignupForm):

    def __init__(self, *args, **kwargs):
        super(CustomSignupForm, self).__init__(*args, **kwargs)
        for field in ('username', 'email', 'password1', 'password2'):
            del self.fields[field].widget.attrs['placeholder']
