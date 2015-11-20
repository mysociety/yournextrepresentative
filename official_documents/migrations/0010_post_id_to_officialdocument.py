# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def post_id_to_post(apps, schema_editor):
    Post = apps.get_model('popolo', 'post')
    Document = apps.get_model('official_documents', 'officialdocument')
    for d in Document.objects.all():
        d.document_post = Post.objects.get(extra__slug=d.post_id)
        d.save()


def post_to_post_id(apps, schema_editor):
    Document = apps.get_model('official_documents', 'officialdocument')
    for d in Document.objects.all():
        d.post_id = d.document_post.extra.slug
        d.save()


class Migration(migrations.Migration):

    dependencies = [
        ('official_documents', '0009_officialdocument_document_post'),
        ('candidates', '0009_migrate_to_django_popolo'),
    ]

    operations = [
        migrations.RunPython(
            post_id_to_post,
            post_to_post_id,
        ),
    ]
