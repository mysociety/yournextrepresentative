from django.test import TestCase

from candidates.models import MaxPopItIds

class MaxPopItTests(TestCase):
    def test_get_max_persons_id(self):
        self.assertEqual(MaxPopItIds.get_max_persons_id(), 0)

    def test_update_max_persons_id(self):
        new_max = 10
        MaxPopItIds.update_max_persons_id(new_max)
        self.assertEqual(MaxPopItIds.get_max_persons_id(), 10)

    def test_update_max_persons_id_less_than_existing(self):
        MaxPopItIds.update_max_persons_id(10)
        self.assertRaises(ValueError, MaxPopItIds.update_max_persons_id, 5)
