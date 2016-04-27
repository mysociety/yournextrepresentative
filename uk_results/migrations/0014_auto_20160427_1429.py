# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0002_update_models_from_upstream'),
        ('uk_results', '0013_auto_20160427_1410'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='candidateresult',
            options={'ordering': ('membership__person',)},
        ),
        migrations.AddField(
            model_name='candidateresult',
            name='membership',
            field=models.ForeignKey(related_name='result', default=1, to='popolo.Membership'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='candidateresult',
            unique_together=set([('result_set', 'membership')]),
        ),
        migrations.RemoveField(
            model_name='candidateresult',
            name='person',
        ),
    ]
