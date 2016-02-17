# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('candidates', '0025_remove_old_post_to_election_m2m_and_rename_new'),
    ]

    operations = [
        migrations.CreateModel(
            name='ComplexPopoloField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('label', models.CharField(help_text='User facing description of the information', max_length=256)),
                ('popolo_array', models.CharField(help_text='Name of the Popolo related type', max_length=256, choices=[('links', 'Links'), ('contact_details', 'Contact Details'), ('identifier', 'Identifier')])),
                ('field_type', models.CharField(help_text='Type of HTML field the user will see', max_length=256, choices=[('text', 'Text Field'), ('url', 'URL Field'), ('email', 'Email Field')])),
                ('info_type_key', models.CharField(help_text='Name of the field in the array that stores the type (note for links, contact_type for contacts, scheme for identifiers)', max_length=100)),
                ('info_type', models.CharField(help_text='Value to put in the info_type_key e.g. twitter', max_length=100)),
                ('old_info_type', models.CharField(max_length=100, blank=True)),
                ('info_value_key', models.CharField(help_text='Name of the field in the array that stores the value, e.g url for links, value for contact_type, identifier for identifiers', max_length=100)),
                ('order', models.IntegerField(blank=True, default=0)),
            ],
        ),
    ]
