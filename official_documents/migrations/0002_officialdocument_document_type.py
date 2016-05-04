# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('official_documents', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='officialdocument',
            name='document_type',
            field=models.CharField(default='Nomination paper', max_length=100, choices=[('nomination_paper', 'Nomination paper')]),
            preserve_default=False,
        ),
    ]
