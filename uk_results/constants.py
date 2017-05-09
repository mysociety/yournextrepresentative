from django.conf import settings

RESULTS_DATE =getattr(settings, 'RESULTS_DATE', "2017-05-04")

MAPIT_URL = "http://mapit.mysociety.org/"
GOV_UK_LA_URL = "https://www.registertovote.service.gov.uk/register-to-vote/local-authority/"

COUNCIL_TYPES = [
    "LBO",
    "DIS",
    "MTD",
    "LGD",
    "UTA",
]


UNCONFIRMED_STATUS = 'unconfirmed'
CONFIRMED_STATUS = 'confirmed'
REJECTED_STATUS = 'rejected'

REPORTED_RESULT_STATUSES = (
    (None, 'Unreviewed'),
    (UNCONFIRMED_STATUS, 'Unconfirmed'),
    (CONFIRMED_STATUS, 'Confirmed'),
    (REJECTED_STATUS, 'Rejected'),
)
