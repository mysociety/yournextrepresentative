# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('images', '0001_initial'),
        ('popolo', '0002_update_models_from_upstream'),
        ('elections', '0003_allow_null_winner_membership_role'),
        ('candidates', '0007_add_result_recorders_group'),
    ]

    operations = [
        migrations.CreateModel(
            name='MembershipExtra',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('base', models.OneToOneField(related_name='extra', to='popolo.Membership')),
                ('election', models.ForeignKey(related_name='candidacies', blank=True, to='elections.Election', null=True)),
                ('party_list_position', models.IntegerField(null=True)),
                ('elected', models.NullBooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='OrganizationExtra',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('register', models.CharField(max_length=512, blank=True)),
                ('base', models.OneToOneField(related_name='extra', to='popolo.Organization')),
                ('slug', models.CharField(max_length=256, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='PersonExtra',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cv', models.TextField(blank=True)),
                ('program', models.TextField(blank=True)),
                ('versions', models.TextField(blank=True)),
                ('base', models.OneToOneField(related_name='extra', to='popolo.Person')),
                ('not_standing', models.ManyToManyField(related_name='persons_not_standing', to='elections.Election')),
            ],
        ),
        migrations.CreateModel(
            name='PartySet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('slug', models.CharField(max_length=256)),
                ('name', models.CharField(max_length=1024)),
                ('parties', models.ManyToManyField(related_name='party_sets', to='popolo.Organization')),
            ],
        ),
        migrations.CreateModel(
            name='PostExtra',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('base', models.OneToOneField(related_name='extra', to='popolo.Post')),
                ('slug', models.CharField(max_length=256, blank=True)),
                ('candidates_locked', models.BooleanField(default=False)),
                ('elections', models.ManyToManyField(related_name='posts', to='elections.Election')),
                ('group', models.CharField(max_length=1024, blank=True)),
                ('party_set', models.ForeignKey(blank=True, to='candidates.PartySet', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='AreaExtra',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('base', models.OneToOneField(related_name='extra', to='popolo.Area')),
                ('type', models.ForeignKey(related_name='areas', blank=True, to='elections.AreaType', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ImageExtra',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('copyright', models.CharField(default='other', max_length=64, blank=True)),
                ('user_notes', models.TextField(blank=True)),
                ('base', models.OneToOneField(related_name='extra', to='images.Image')),
                ('md5sum', models.CharField(max_length=32, blank=True)),
                ('uploading_user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('user_copyright', models.CharField(max_length=128, blank=True)),
                ('notes', models.TextField(blank=True)),
            ],
        ),
    ]
