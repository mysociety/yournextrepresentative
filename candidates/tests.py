from django_webtest import WebTest

class TestConstituencyFinderView(WebTest):

    def test_front_page(self):
        response = self.app.get('/')
        # Check that there is a form on that page
        form = response.form
