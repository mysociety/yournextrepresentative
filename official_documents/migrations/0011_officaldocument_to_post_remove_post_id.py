# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('official_documents', '0010_post_id_to_officialdocument'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='officialdocument',
            name='post_id',
        ),
        migrations.RenameField(
            model_name='officialdocument',
            old_name='document_post',
            new_name='post',
        ),
    ]
