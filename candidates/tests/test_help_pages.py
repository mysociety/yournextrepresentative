from django_webtest import WebTest


class TestHelpPages(WebTest):
    def test_photo_policy(self):
        response = self.app.get('/help/photo-policy')
        self.assertContains(response, '<h1>Photo policy</h1>')
