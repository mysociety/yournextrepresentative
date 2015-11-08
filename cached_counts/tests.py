# -*- coding: utf-8 -*-

from mock import patch, MagicMock
import re

from django.core.management import call_command
from django_webtest import WebTest

from candidates.tests.test_create_person import mock_create_person
from candidates.tests.fake_popit import (
    fake_mp_post_search_results, FakePostCollection
)

from .models import CachedCount


def create_initial_counts(extra=()):
    initial_counts = (
        {
            'election': '2015',
            'count_type': 'post',
            'name': 'Dulwich and West Norwood',
            'count': 10,
            'object_id': '65808'
        },
        {
            'election': '2015',
            'count_type': 'post',
            'name': 'Camberwell and Peckham',
            'count': 3,
            'object_id': '65913'
        },
        {
            'election': '2015',
            'count_type': 'post',
            'name': u'Ynys Môn',
            'count': 0,
            'object_id': '66115'
        },
        {
            'election': '2015',
            'count_type': 'party',
            'name': 'Labour',
            'count': 0,
            'object_id': 'party:53'
        },
        {
            'election': '2015',
            'count_type': 'total',
            'name': 'total',
            'count': 1024,
            'object_id': '2015'
        },
        {
            'election': '2010',
            'count_type': 'total',
            'name': 'total',
            'count': 1500,
            'object_id': '2010'
        },
    )
    initial_counts = initial_counts + extra

    for count in initial_counts:
        CachedCount(**count).save()

class CachedCountTestCase(WebTest):
    def setUp(self):
        create_initial_counts()

    def test_increment_count(self):
        self.assertEqual(CachedCount.objects.get(object_id='party:53').count, 0)
        self.assertEqual(CachedCount.objects.get(object_id='65808').count, 10)
        mock_create_person()
        self.assertEqual(CachedCount.objects.get(object_id='65808').count, 11)
        self.assertEqual(CachedCount.objects.get(object_id='party:53').count, 1)

    def test_reports_top_page(self):
        response = self.app.get('/numbers/')
        self.assertEqual(response.status_code, 200)

    def test_attention_needed_page(self):
        response = self.app.get('/numbers/attention-needed')
        rows = [
            tuple(unicode(td) for td in row.find_all('td'))
            for row in response.html.find_all('tr')
        ]
        self.assertEqual(
            rows,
            [
                (u'<td><a href="/election/2015/post/66115/ynys-mon">Ynys M\xf4n</a></td>',
                 u'<td>0</td>'),
                (u'<td><a href="/election/2015/post/65913/camberwell-and-peckham">Camberwell and Peckham</a></td>',
                 u'<td>3</td>'),
                (u'<td><a href="/election/2015/post/65808/dulwich-and-west-norwood">Dulwich and West Norwood</a></td>',
                 u'<td>10</td>')
            ]
        )
