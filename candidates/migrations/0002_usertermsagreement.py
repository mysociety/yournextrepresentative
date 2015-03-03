# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('candidates', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserTermsAgreement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('assigned_to_dc', models.BooleanField(default=False)),
                ('user', models.OneToOneField(related_name='terms_agreement', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
