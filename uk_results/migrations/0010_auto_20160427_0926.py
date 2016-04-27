# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('uk_results', '0009_auto_20160427_0858'),
    ]

    operations = [
        migrations.RenameField(
            model_name='councilelectionresultset',
            old_name='confirm_source',
            new_name='review_source',
        ),
        migrations.RemoveField(
            model_name='councilelectionresultset',
            name='confirmed_by',
        ),
        migrations.RemoveField(
            model_name='councilelectionresultset',
            name='is_rejected',
        ),
        migrations.RemoveField(
            model_name='councilelectionresultset',
            name='rejected_by',
        ),
        migrations.RemoveField(
            model_name='councilelectionresultset',
            name='rejected_source',
        ),
        migrations.AddField(
            model_name='councilelectionresultset',
            name='review_status',
            field=models.CharField(blank=True, max_length=100, choices=[(b'unconfirmed', b'Unconfirmed'), (b'confirmed', b'Confirmed'), (b'rejected', b'Rejected')]),
        ),
        migrations.AddField(
            model_name='councilelectionresultset',
            name='reviewed_by',
            field=models.ForeignKey(related_name='results_reviewed', to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
