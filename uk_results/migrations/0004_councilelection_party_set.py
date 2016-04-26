# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0030_merge'),
        ('uk_results', '0003_auto_20160425_2151'),
    ]

    operations = [
        migrations.AddField(
            model_name='councilelection',
            name='party_set',
            field=models.ForeignKey(default=1, to='candidates.PartySet'),
            preserve_default=False,
        ),
    ]
