from __future__ import unicode_literals

from django import forms

from allauth.account.forms import LoginForm

from django.utils.translation import ugettext_lazy as _


class CustomLoginForm(LoginForm):

    def __init__(self, *args, **kwargs):
        super(CustomLoginForm, self).__init__(*args, **kwargs)
        self.fields['login'].label = _('Username or email address')
