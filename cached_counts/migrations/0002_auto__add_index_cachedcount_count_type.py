# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'CachedCount', fields ['count_type']
        db.create_index(u'cached_counts_cachedcount', ['count_type'])


    def backwards(self, orm):
        # Removing index on 'CachedCount', fields ['count_type']
        db.delete_index(u'cached_counts_cachedcount', ['count_type'])


    models = {
        u'cached_counts.cachedcount': {
            'Meta': {'ordering': "['-count']", 'object_name': 'CachedCount'},
            'count': ('django.db.models.fields.IntegerField', [], {}),
            'count_type': ('django.db.models.fields.CharField', [], {'max_length': '100', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'object_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        }
    }

    complete_apps = ['cached_counts']