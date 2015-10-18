# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('official_documents', '0013_election_id_to_election_model'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='officialdocument',
            name='election',
        ),
    ]
