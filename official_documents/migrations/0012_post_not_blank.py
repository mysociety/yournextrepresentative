# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('official_documents', '0011_officaldocument_to_post_remove_post_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='officialdocument',
            name='post',
            field=models.ForeignKey(to='popolo.Post'),
        ),
    ]
