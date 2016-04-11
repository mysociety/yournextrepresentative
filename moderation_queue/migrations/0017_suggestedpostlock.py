# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0028_auto_20160411_1055'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('moderation_queue', '0016_remove_queuedimage_popit_person_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='SuggestedPostLock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('justification', models.TextField(help_text="e.g I've reviewed the nomination paper for this area", blank=True)),
                ('post_extra', models.ForeignKey(to='candidates.PostExtra')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
