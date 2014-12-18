# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CachedCount'
        db.create_table(u'cached_counts_cachedcount', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('count_type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('count', self.gf('django.db.models.fields.IntegerField')()),
            ('object_id', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
        ))
        db.send_create_signal(u'cached_counts', ['CachedCount'])


    def backwards(self, orm):
        # Deleting model 'CachedCount'
        db.delete_table(u'cached_counts_cachedcount')


    models = {
        u'cached_counts.cachedcount': {
            'Meta': {'object_name': 'CachedCount'},
            'count': ('django.db.models.fields.IntegerField', [], {}),
            'count_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'object_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        }
    }

    complete_apps = ['cached_counts']