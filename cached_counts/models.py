from django.db import models
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify

class CachedCount(models.Model):
    """
    Fairly generic model for storing counts of various sorts.

    The object_id is used for linking through to the relevant URL.
    """

    count_type = models.CharField(blank=False, max_length=100, db_index=True)
    name = models.CharField(blank=False, max_length=100)
    count = models.IntegerField(blank=False, null=False)
    object_id = models.CharField(blank=True, max_length=100)

    class Meta:
        ordering = ['-count', 'name']

    @classmethod
    def total_2015(cls):
        print cls.objects.get(name="total_2015")
        return cls.objects.get(name="total_2015").count

    @property
    def object_url(self):
        if self.count_type == "constituency":
            return reverse('constituency', kwargs={
                'mapit_area_id': self.object_id,
                'ignored_slug': slugify(self.name)
            })
