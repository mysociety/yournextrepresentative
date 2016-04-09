from __future__ import print_function, unicode_literals

from datetime import datetime
from random import randint
import sys

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from candidates.models import ImageExtra


def print_image_extra_data(image_extra):
    print("  [extra] copyright:", image_extra.copyright)
    print("  [extra] uploading_user:", image_extra.uploading_user)
    print("  [extra] user_notes:", image_extra.user_notes)
    print("  [extra] md5sum:", image_extra.md5sum)
    print("  [extra] user_copyright:", image_extra.user_copyright)
    print("  [extra] notes:", image_extra.notes)
    base = image_extra.base
    print("  [base] source:", base.source)
    print("  [base] image.path:", base.image.path)
    print("  [base] image.url:", base.image.url)

class Command(BaseCommand):

    help = "Deduplicate images that have the same MD5sum"

    # def add_arguments(self, parser):
    #     parser.add_argument(
    #         '--person-id',
    #         help='Only record the current version for the person with this ID'
    #     )
    #     parser.add_argument(
    #         '--source', help='The source of information for this other name'
    #     )

    def handle(self, *args, **options):
        for md5sum_and_count in ImageExtra.objects \
                .values('md5sum', 'base__content_type_id', 'base__object_id') \
                .annotate(dup_count=Count('md5sum')):
            if md5sum_and_count['dup_count'] <= 1:
                continue
            print("count is:", md5sum_and_count['dup_count'])
            md5sum = md5sum_and_count['md5sum']
            image_extras = ImageExtra.objects \
                .filter(md5sum=md5sum).order_by('id').select_related('base')
            image_extras = list(image_extras)
            image_extra_to_preserve = image_extras.pop(0)
            image_to_preserve = image_extra_to_preserve.base
            print("==================+++")
            for image_extra in image_extras:
                print("  --- to preserve:")
                print_image_extra_data(image_extra_to_preserve)
                print("  --- to delete:")
                print_image_extra_data(image_extra)
