from django_webtest import WebTest

from usersettings.shortcuts import get_current_usersettings

from .settings import SettingsMixin


class TestLanguageSwitcher(SettingsMixin, WebTest):


    def test_switch_language(self):
        response = self.app.get('/')

        response.mustcontain('Open data API')

        form = response.forms['language_switcher']
        form['language'] = 'cy-gb'
        response = form.submit().follow()

        response.mustcontain('Amdanom Ni')

    def test_switch_language_in_settings(self):
        response = self.app.get('/')

        response.mustcontain('Open data API')

        site_settings = get_current_usersettings()
        site_settings.LANGUAGE = 'cy-gb'
        site_settings.save()

        response = self.app.get('/')

        response.mustcontain('Amdanom Ni')

    def test_switch_language_overrides_settings_lang(self):
        site_settings = get_current_usersettings()
        site_settings.LANGUAGE = 'fr'
        site_settings.save()

        response = self.app.get('/')

        response.mustcontain('API open data')

        form = response.forms['language_switcher']
        form['language'] = 'cy-gb'
        response = form.submit().follow()

        response.mustcontain('Amdanom Ni')

    def test_accept_lang_overrides_settings_lang(self):
        headers = {'Accept-Language': 'en'}
        response = self.app.get('/')

        response.mustcontain('Open data API')

        site_settings = get_current_usersettings()
        site_settings.LANGUAGE = 'cy-gb'
        site_settings.save()

        response = self.app.get('/', headers=headers)

        response.mustcontain('Open data API')
