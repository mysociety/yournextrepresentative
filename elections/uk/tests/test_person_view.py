from nose.plugins.attrib import attr

from candidates.tests.person_view_shared_tests_mixin import PersonViewSharedTestsMixin


@attr(country='uk')
class TestPersonView(PersonViewSharedTestsMixin):
    pass
