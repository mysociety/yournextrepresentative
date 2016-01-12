# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0002_update_models_from_upstream'),
        ('candidates', '0014_make_extra_slugs_unique'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExtraField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=256)),
                ('type', models.CharField(max_length=64, choices=[(b'line', b'A single line of text'), (b'longer-text', b'One or more paragraphs of text'), (b'url', b'A URL')])),
                ('label', models.CharField(max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name='PersonExtraFieldValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('value', models.TextField(blank=True)),
                ('field', models.ForeignKey(to='candidates.ExtraField')),
                ('person', models.ForeignKey(related_name='extra_field_values', to='popolo.Person')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='personextrafieldvalue',
            unique_together=set([('person', 'field')]),
        ),
    ]
