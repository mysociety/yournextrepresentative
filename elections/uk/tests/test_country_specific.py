from mock import patch

from django.test import TestCase

from nose.plugins.attrib import attr

from candidates.election_specific import additional_merge_actions
from candidates.tests import factories

@attr(country='uk')
class TestUKSpecificOverride(TestCase):

    @patch('elections.uk.lib.additional_merge_actions')
    def test_uk_version_is_actually_called(self, mock_additional_merge_actions):
        primary = factories.PersonExtraFactory(base__name='Alice')
        secondary = factories.PersonExtraFactory(base__name='Bob')
        additional_merge_actions(primary, secondary)
        mock_additional_merge_actions.assert_called
