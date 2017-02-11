from __future__ import print_function, unicode_literals

import sys

from django.core.management.base import BaseCommand

from candidates.models import check_paired_models


class Command(BaseCommand):

    def handle(self, *args, **options):
        errors = check_paired_models()
        if errors:
            for error in errors:
                print(error)
            sys.exit(1)
