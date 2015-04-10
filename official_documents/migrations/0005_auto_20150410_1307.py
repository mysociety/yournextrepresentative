# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('official_documents', '0004_auto_20150410_1054'),
    ]

    operations = [
        migrations.AlterField(
            model_name='officialdocument',
            name='source_url',
            field=models.URLField(help_text=b'The page that links to this document', max_length=1000, blank=True),
            preserve_default=True,
        ),
    ]
