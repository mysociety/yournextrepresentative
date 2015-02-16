import unittest

from django.test import TestCase

from candidates.tests.test_create_person import mock_create_person

from .models import CachedCount

def create_initial_counts(extra=()):
    initial_counts = (
        {
            'count_type': 'constituency',
            'name': 'Dulwich and West Norwood',
            'count': 10,
            'object_id': '65808'
        },
        {
            'count_type': 'party',
            'name': 'Labour',
            'count': 0,
            'object_id': 'party:53'
        },
    )
    initial_counts = initial_counts + extra

    for count in initial_counts:
        CachedCount(**count).save()

class CachedCountTechCase(TestCase):
    def setUp(self):
        create_initial_counts()

    def test_object_urls(self):
        for count in CachedCount.objects.filter(count_type='constituency'):
            self.assertTrue(count.object_url)

    def test_increment_count(self):
        self.assertEqual(CachedCount.objects.get(object_id='party:53').count, 0)
        self.assertEqual(CachedCount.objects.get(object_id='65808').count, 10)
        mock_create_person()
        self.assertEqual(CachedCount.objects.get(object_id='65808').count, 11)
        self.assertEqual(CachedCount.objects.get(object_id='party:53').count, 1)
