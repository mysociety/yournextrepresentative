# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('moderation_queue', '0012_auto_20150717_0811'),
    ]

    operations = [
        migrations.AlterField(
            model_name='queuedimage',
            name='why_allowed',
            field=models.CharField(default='other', max_length=64, choices=[('public-domain', 'This photograph is free of any copyright restrictions'), ('copyright-assigned', 'I own copyright of this photo and I assign the copyright to Democracy Club Limited in return for it being displayed on this site'), ('profile-photo', "This is the candidate's public profile photo from social media (e.g. Twitter, Facebook) or their official campaign page"), ('other', 'Other')]),
        ),
    ]
