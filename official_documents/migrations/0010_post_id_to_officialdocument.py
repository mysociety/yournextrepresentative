# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def post_id_to_post(apps, schema_editor):
    Post = apps.get_model('popolo', 'post')
    Document = apps.get_model('official_documents', 'officialdocument')
    for la in Document.objects.all():
        la.document_post = Post.objects.get(pk=la.post_id)
        la.save()


def post_to_post_id(apps, schema_editor):
    Document = apps.get_model('official_documents', 'officialdocument')
    for la in Document.objects.all():
        la.post_id = la.document_post.id
        la.save()


class Migration(migrations.Migration):

    dependencies = [
        ('official_documents', '0009_officialdocument_document_post'),
    ]

    operations = [
        migrations.RunPython(
            post_id_to_post,
            post_to_post_id,
        ),
    ]
