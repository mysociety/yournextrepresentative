from django_webtest import WebTest


class TestHelpPages(WebTest):
    def test_about_page(self):
        response = self.app.get('/help/about')
        self.assertContains(response, '<h1>About this site</h1>')

    def test_about_page_links_to_privacy_policy(self):
        response = self.app.get('/help/about')
        self.assertContains(response, '<a href="/help/privacy">here</a>')

    def test_about_page_links_to_photo_policy(self):
        response = self.app.get('/help/about')
        self.assertContains(response, '<a href="/help/photo-policy">here</a>')

    def test_privacy_policy(self):
        response = self.app.get('/help/privacy')
        self.assertContains(response, '<h1>Privacy policy</h1>')

    def test_photo_policy(self):
        response = self.app.get('/help/photo-policy')
        self.assertContains(response, '<h1>Photo policy</h1>')
