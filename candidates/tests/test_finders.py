from urlparse import urlsplit

from django_webtest import WebTest

class TestConstituencyPostcodeFinderView(WebTest):

    def test_front_page(self):
        response = self.app.get('/')
        # Check that there is a form on that page
        response.forms['form-postcode']
        response.forms['form-name']

    def test_valid_postcode_redirects_to_constituency(self):
        response = self.app.get('/')
        form = response.forms['form-postcode']
        form['postcode'] = 'SW1A 1AA'
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(
            split_location.path,
            '/constituency/65759/cities-of-london-and-westminster'
        )

    def test_unknown_postcode_returns_to_finder_with_error(self):
        response = self.app.get('/')
        form = response.forms['form-postcode']
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
        form = response.forms['form-postcode']
        # This looks like a postcode to the usual postcode-checking
        # regular expressions, but doesn't actually exist
        form['postcode'] = 'foo bar'
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(split_location.path, '/')
        self.assertEqual(split_location.query, 'bad_postcode=foo%20bar')


class TestConstituencyNameFinderView(WebTest):

    def test_pick_constituency_name(self):
        response = self.app.get('/')
        form = response.forms['form-name']
        form['constituency'] = '66044'
        response = form.submit()
        self.assertEqual(response.status_code, 302)
        split_location = urlsplit(response.location)
        self.assertEqual(
            split_location.path,
            '/constituency/66044/epping-forest'
        )
