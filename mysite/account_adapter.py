from __future__ import unicode_literals

from allauth.account.adapter import DefaultAccountAdapter
from usersettings.shortcuts import get_current_usersettings

class CheckIfAllowedNewUsersAccountAdapter(DefaultAccountAdapter):

    def is_open_for_signup(self, request):
        """
        Checks whether or not the site is open for signups.

        Next to simply returning True/False you can also intervene the
        regular flow by raising an ImmediateHttpResponse

        (Comment reproduced from the overridden method.)
        """

        userconf = get_current_usersettings()
        if userconf.NEW_ACCOUNTS_ALLOWED:
            return True

        return False
