from django.db import models
from django.contrib.postgres.fields import ArrayField


class AreaType(models.Model):
    name = models.CharField(max_length=128)
    source = models.CharField(max_length=128, blank=True,
                              help_text="e.g MapIt")

    def __unicode__(self):
        return self.name


class Election(models.Model):
    slug = models.CharField(max_length=128)
    for_post_role = models.CharField(max_length=128)
    winner_membership_role = models.CharField(max_length=128, blank=True)
    candidate_membership_role = models.CharField(max_length=128)
    election_date = models.DateField()
    candidacy_start_date = models.DateField()
    name = models.CharField(max_length=128)
    current = models.BooleanField()
    use_for_candidate_suggestions = models.BooleanField(default=False)
    party_membership_start_date = models.DateField()
    party_membership_end_date = models.DateField()
    area_types = models.ManyToManyField(AreaType)
    area_generation = models.CharField(max_length=128, blank=True)
    organization_id = models.CharField(max_length=128)
    organization_name = models.CharField(max_length=128, blank=True)
    post_id_format = models.CharField(max_length=128)
    party_lists_in_use = models.BooleanField(default=False)
    default_party_list_members_to_show = models.IntegerField(default=0)
    show_official_documents = models.BooleanField(default=False)
    ocd_division = models.CharField(max_length=250, blank=True)

    description = models.CharField(max_length=500, blank=True)

    def __unicode__(self):
        return self.name
