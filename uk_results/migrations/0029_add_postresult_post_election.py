# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0032_migrate_org_slugs'),
        ('uk_results', '0028_auto_20170503_1633'),
    ]

    operations = [
        migrations.AddField(
            model_name='postresult',
            name='post_election',
            field=models.ForeignKey(
                null=True, to='candidates.PostExtraElection'),
            preserve_default=False,
        ),
    ]

