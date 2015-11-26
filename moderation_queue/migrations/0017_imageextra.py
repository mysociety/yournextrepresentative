# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('images', '0001_initial'),
        ('moderation_queue', '0016_remove_queuedimage_popit_person_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='ImageExtra',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('copyright', models.CharField(default=b'other', max_length=64, choices=[(b'public-domain', 'This photograph is free of any copyright restrictions'), (b'copyright-assigned', 'I own copyright of this photo and I assign the copyright to Democracy Club Limited in return for it being displayed on this site'), (b'profile-photo', "This is the candidate's public profile photo from social media (e.g. Twitter, Facebook) or their official campaign page"), (b'other', 'Other')])),
                ('user_notes', models.TextField(blank=True)),
                ('base', models.OneToOneField(related_name='extra', to='images.Image')),
                ('uploading_user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
    ]
