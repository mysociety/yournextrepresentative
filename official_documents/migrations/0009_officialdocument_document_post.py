# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0002_update_models_from_upstream'),
        ('official_documents', '0008_set_default_election'),
    ]

    operations = [
        migrations.AddField(
            model_name='officialdocument',
            name='document_post',
            field=models.ForeignKey(to='popolo.Post', blank=True, null=True),
            preserve_default=False,
        ),
    ]
