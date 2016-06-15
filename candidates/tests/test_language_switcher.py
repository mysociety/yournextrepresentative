from django_webtest import WebTest

from .settings import SettingsMixin


class TestLanguageSwitcher(SettingsMixin, WebTest):

    def test_switch_language(self):
        response = self.app.get('/')

        response.mustcontain('Open data API')

        form = response.forms['language_switcher']
        form['language'] = 'cy-gb'
        response = form.submit().follow()

        response.mustcontain('Amdanom Ni')
