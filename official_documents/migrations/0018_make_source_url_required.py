# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('official_documents', '0017_update_django_extensions_datetime_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='officialdocument',
            name='source_url',
            field=models.URLField(help_text='The page that links to this document', max_length=1000),
        ),
    ]
