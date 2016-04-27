# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0002_update_models_from_upstream'),
        ('uk_results', '0010_auto_20160427_0926'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('confirmed', models.BooleanField(default=False)),
                ('post', models.ForeignKey(to='popolo.Post')),
            ],
        ),
        migrations.AlterField(
            model_name='resultset',
            name='post',
            field=models.ForeignKey(related_name='result_sets', to='uk_results.PostResult'),
        ),
    ]
