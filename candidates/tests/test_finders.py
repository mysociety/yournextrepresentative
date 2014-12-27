from mock import patch, Mock

from urlparse import urlsplit

from django_webtest import WebTest

def fake_requests_for_mapit(url):
    """Return reduced MapIt output for some known URLs"""
    if url == 'http://mapit.mysociety.org/postcode/SW1A 1AA':
        status_code = 200
        json_result = {
            "shortcuts": {
                "WMC": 65759,
            },
        }
    elif url == 'http://mapit.mysociety.org/postcode/CB2 8RQ':
        status_code = 404
        json_result = {
            "code": 404,
            "error": "No Postcode matches the given query."
        }
    elif url == 'http://mapit.mysociety.org/postcode/foo bar':
        status_code = 400
        json_result = {
            "code": 400,
            "error": "Postcode 'FOOBAR' is not valid."
        }
    else:
        raise Exception("URL that hasn't been mocked yet: " + url)
    return Mock(**{
        'json.return_value': json_result,
        'status_code': status_code
    })

@patch('candidates.views.requests')
class TestConstituencyPostcodeFinderView(WebTest):

    def test_front_page(self, mock_requests):
        response = self.app.get('/')
        # Check that there is a form on that page
        response.forms['form-postcode']
        response.forms['form-name']

    def test_valid_postcode_redirects_to_constituency(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_mapit
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

    def test_unknown_postcode_returns_to_finder_with_error(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_mapit
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


    def test_nonsense_postcode_returns_to_finder_with_error(self, mock_requests):
        mock_requests.get.side_effect = fake_requests_for_mapit
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

    def test_post_no_constituency_selected(self):
        response = self.app.get('/')
        form = response.forms['form-name']
        form['constituency'] = 'none'
        response = form.submit()
        self.assertEqual(response.status_code, 200)
        self.assertIn('You must select a constituency', response)
