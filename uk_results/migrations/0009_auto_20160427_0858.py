# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('uk_results', '0008_auto_20160426_1629'),
    ]

    operations = [
        migrations.AddField(
            model_name='councilelectionresultset',
            name='is_rejected',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='councilelectionresultset',
            name='rejected_by',
            field=models.ForeignKey(related_name='results_rejected', to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='councilelectionresultset',
            name='rejected_source',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='councilelectionresultset',
            name='confirmed_by',
            field=models.ForeignKey(related_name='results_confirmed', to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
