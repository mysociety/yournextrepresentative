from datetime import date, timedelta

from django.conf import settings

date_in_near_future = date.today() + timedelta(days=14)

FOUR_YEARS_IN_DAYS = 1462

election_date_before = lambda r: {
    'DATE_TODAY': date.today()
}
election_date_on_election_day = lambda r: {
    'DATE_TODAY': date_in_near_future
}
election_date_after = lambda r: {
    'DATE_TODAY': date.today() + timedelta(days=28)
}

processors = settings.TEMPLATE_CONTEXT_PROCESSORS

processors_before = processors + \
    ("candidates.tests.dates.election_date_before",)
processors_on_election_day = processors + \
    ("candidates.tests.dates.election_date_on_election_day",)
processors_after = processors + \
    ("candidates.tests.dates.election_date_after",)
