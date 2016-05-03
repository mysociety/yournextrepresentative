# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0020_cr_add_reelection_field'),
    ]

    operations = [
        migrations.CreateModel(
            name='SimplePopoloField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256, choices=[('name', 'Name'), ('family_name', 'Family Name'), ('given_name', 'Given Name'), ('additional_name', 'Additional Name'), ('honorific_prefix', 'Honorific Prefix'), ('honorific_suffix', 'Honorific Suffix'), ('patronymic_name', 'Patronymic Name'), ('sort_name', 'Sort Name'), ('email', 'Email'), ('gender', 'Gender'), ('birth_date', 'Birth Date'), ('death_date', 'Death Date'), ('summary', 'Summary'), ('biography', 'Biography'), ('national_identity', 'National Identity')])),
                ('label', models.CharField(max_length=256)),
                ('required', models.BooleanField(default=False)),
                ('info_type_key', models.CharField(max_length=256, choices=[('text', 'Text Field'), ('email', 'Email Field')])),
                ('order', models.IntegerField(blank=True)),
            ],
        ),
    ]
