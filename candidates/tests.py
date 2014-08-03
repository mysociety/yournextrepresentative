from urlparse import urlsplit

from django_webtest import WebTest

class TestConstituencyFinderView(WebTest):

    def test_front_page(self):
        response = self.app.get('/')
        # Check that there is a form on that page
        form = response.form

    def test_valid_postcode_redirects_to_constituency(self):
        response = self.app.get('/')
        form = response.form
        form['postcode'] = 'SW1A 1AA'
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(
            split_location.path,
            '/constituency/Cities%20of%20London%20and%20Westminster'
        )

    def test_unknown_postcode_returns_to_finder_with_error(self):
        response = self.app.get('/')
        form = response.form
        # This looks like a postcode to the usual postcode-checking
        # regular expressions, but doesn't actually exist
        form['postcode'] = 'CB2 8RQ'
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(split_location.path, '/')
        self.assertEqual(split_location.query, 'bad_postcode=CB2%208RQ')


    def test_nonsense_postcode_returns_to_finder_with_error(self):
        response = self.app.get('/')
        form = response.form
        # This looks like a postcode to the usual postcode-checking
        # regular expressions, but doesn't actually exist
        form['postcode'] = 'foo bar'
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(split_location.path, '/')
        self.assertEqual(split_location.query, 'bad_postcode=foo%20bar')


class TestConstituencyDetailView(WebTest):

    def test_any_constituency_page(self):
        # Just a smoke test for the moment:
        self.app.get('/constituency/Dulwich%20and%20West%20Norwood')
