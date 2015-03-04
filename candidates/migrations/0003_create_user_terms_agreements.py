# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def create_user_terms_agreements(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserTermsAgreement = apps.get_model('candidates', 'UserTermsAgreement')
    for u in User.objects.all():
        UserTermsAgreement.objects.get_or_create(user=u)


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0002_usertermsagreement'),
    ]

    operations = [
        migrations.RunPython(
            create_user_terms_agreements
        )
    ]
