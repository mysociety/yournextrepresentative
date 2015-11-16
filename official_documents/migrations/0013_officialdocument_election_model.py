# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0007_rename_new_organization_to_organization'),
        ('official_documents', '0012_post_not_blank'),
    ]

    operations = [
        migrations.AddField(
            model_name='officialdocument',
            name='election_model',
            field=models.ForeignKey(blank=True, to='elections.Election', null=True),
        ),
    ]
