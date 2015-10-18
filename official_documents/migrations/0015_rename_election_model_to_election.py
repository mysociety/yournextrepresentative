# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('official_documents', '0014_remove_officialdocument_election'),
    ]

    operations = [
        migrations.RenameField(
            model_name='officialdocument',
            old_name='election_model',
            new_name='election',
        ),
    ]
