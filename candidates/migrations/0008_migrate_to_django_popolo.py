# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.db import migrations

from popolo.importers.popit import PopItImporter

class YNRPopItImporter(PopItImporter):

    def __init__(self, apps, schema_editor):
        self.apps = apps
        self.schema_editor = schema_editor

    def get_model_class(self, app_label, model_name):
        return self.apps.get_model(app_label, model_name)

    def update_person(self, person_data):
        new_person_data = person_data.copy()
        # There are quite a lot of summary fields in PopIt that are
        # way longer than 1024 characters.
        new_person_data['summary'] = (person_data.get('summary') or '')[:1024]
        # Surprisingly, quite a lot of PopIt email addresses have
        # extraneous whitespace in them, so strip any out to avoid
        # the 'Enter a valid email address' ValidationError on saving:
        email = person_data.get('email') or None
        if email:
            email = re.sub(r'\s*', '', email)
        new_person_data['email'] = email
        return super(YNRPopItImporter, self).update_person(new_person_data)

    def make_contact_detail_dict(self, contact_detail_data):
        new_contact_detail_data = contact_detail_data.copy()
        # There are some contact types that are used in PopIt that are
        # longer than 12 characters...
        new_contact_detail_data['type'] = contact_detail_data['type'][:12]
        return super(YNRPopItImporter, self).make_contact_detail_dict(new_contact_detail_data)

    def make_link_dict(self, link_data):
        new_link_data = link_data.copy()
        # There are some really long URLs in PopIt, which exceed the
        # 200 character limit in django-popolo.
        new_link_data['url'] = new_link_data['url'][:200]
        return super(YNRPopItImporter, self).make_link_dict(new_link_data)


def import_from_popit(apps, schema_editor):
    importer = YNRPopItImporter(apps, schema_editor)
    filename = '/home/mark/yournextrepresentative/export.json'
    importer.import_from_export_json(filename)


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0007_add_result_recorders_group'),
        ('popolo', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(import_from_popit),
    ]
