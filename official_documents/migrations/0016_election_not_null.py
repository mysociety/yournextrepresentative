# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('official_documents', '0015_rename_election_model_to_election'),
    ]

    operations = [
        migrations.AlterField(
            model_name='officialdocument',
            name='election',
            field=models.ForeignKey(to='elections.Election'),
        ),
    ]
