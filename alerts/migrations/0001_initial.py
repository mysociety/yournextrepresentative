# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('target_object_id', models.CharField(max_length=255, null=True, blank=True)),
                ('action', models.CharField(max_length=100, choices=[('created', 'Created'), ('updated', 'Updated'), ('deleted', 'Deleted'), ('image_update', 'Images'), ('all', 'All')])),
                ('frequency', models.CharField(max_length=100, choices=[('hourly', 'Hourly'), ('daily', 'Daily')])),
                ('last_sent', models.DateTimeField()),
                ('enabled', models.BooleanField(default=True)),
                ('target_content_type', models.ForeignKey(related_name='alert_target', blank=True, to='contenttypes.ContentType', null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
