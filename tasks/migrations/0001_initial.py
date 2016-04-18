# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0002_update_models_from_upstream'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PersonTask',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('task_field', models.CharField(max_length=100, blank=True)),
                ('task_priority', models.IntegerField(default=1, null=True, blank=True)),
                ('bonus_points', models.IntegerField(default=1, null=True, blank=True)),
                ('couldnt_find_count', models.IntegerField(default=0, null=True, blank=True)),
                ('finder', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
                ('person', models.ForeignKey(to='popolo.Person')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
                'get_latest_by': 'modified',
            },
        ),
    ]
