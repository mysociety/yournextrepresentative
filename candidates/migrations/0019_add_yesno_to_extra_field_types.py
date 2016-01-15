# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0018_cr_add_important_posts_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extrafield',
            name='type',
            field=models.CharField(max_length=64, choices=[(b'line', b'A single line of text'), (b'longer-text', b'One or more paragraphs of text'), (b'url', b'A URL'), (b'yesno', b"A Yes/No/Don't know dropdown")]),
        ),
    ]
