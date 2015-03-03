# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def forward_to_why_allowed(apps, schema_editor):
    QueuedImage = apps.get_model('moderation_queue', 'QueuedImage')
    for qi in QueuedImage.objects.all():
        if qi.public_domain:
            qi.why_allowed = 'public-domain'
        elif qi.use_allowed_by_owner:
            qi.why_allowed = 'copyright-assigned'
        else:
            qi.why_allowed = 'other'
        qi.save()

def backwards_from_why_allowed(apps, schema_editor):
    QueuedImage = apps.get_model('moderation_queue', 'QueuedImage')
    for qi in QueuedImage.objects.all():
        if qi.why_allowed == 'public-domain':
            qi.public_domain = True
        elif qi.why_allowed == 'copyright-assigned':
            qi.use_allowed_by_owner = True
        qi.save()

class Migration(migrations.Migration):

    dependencies = [
        ('moderation_queue', '0004_queuedimage_why_allowed'),
    ]

    operations = [
        migrations.RunPython(
            forward_to_why_allowed,
            backwards_from_why_allowed,
        )
    ]
