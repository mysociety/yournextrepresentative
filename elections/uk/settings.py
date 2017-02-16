from __future__ import unicode_literals

MAPIT_BASE_URL = 'http://mapit.democracyclub.org.uk/'

SITE_OWNER = 'Democracy Club'
COPYRIGHT_HOLDER = 'Democracy Club Limited'


INSTALLED_APPS = [
    'bulk_adding',
    'uk_results',
]

TEMPLATE_CONTEXT_PROCESSORS = (
    "uk_results.context_processors.show_results_feature",
)
