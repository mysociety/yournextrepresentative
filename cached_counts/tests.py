from django.test import TestCase

from .models import CachedCount

class CachedCountTechCase(TestCase):
    def setUp(self):
        initial_counts = (
            {
                'count_type': 'constituency',
                'name': 'South Norfolk',
                'count': 10,
                'object_id': '65666'
            },
            {
                'count_type': 'party',
                'name': 'Labour',
                'count': 0,
                'object_id': 'party:53'
            },
        )
        for count in initial_counts:
            CachedCount(**count).save()

    def test_object_urls(self):
        for count in CachedCount.objects.filter(count_type='constituency'):
            self.assertTrue(count.object_url)
