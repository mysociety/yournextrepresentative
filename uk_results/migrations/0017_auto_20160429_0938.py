# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

PARTY_COLOURS = {
    'party:52': {
        'name': "Conservative and Unionist Party",
        'hex': "#0087DC",
    },
    'party:53': {
        'name': "Labour Party",
        'hex': "#D50000",
    },
    'party:63': {
        'name': "Green Party",
        'hex': "#008066",
    },
    'party:85': {
        'name': "UK Independence Party (UKIP)",
        'hex': "#B3009D",
    },
    'party:90': {
        'name': "Liberal Democrats",
        'hex': "#B3009D",
    },
    'party:77': {
        'name': "Plaid Cymru",
        'hex': "#3F8428",
    },
    'party:102': {
        'name': "Scottish National Party",
        'hex': "#FFF95D",
    },
}

def add_party_colours(apps, schema_editor):
    PartyWithColour = apps.get_model("uk_results", "PartyWithColour")
    Organization = apps.get_model("popolo", "Organization")
    for party_id, party_info in PARTY_COLOURS.items():
        try:
            party = Organization.objects.get(extra__slug=party_id)
            PartyWithColour.objects.get_or_create(
                party=party,
                defaults={"hex_value": party_info['hex']}
            )
        except:
            pass


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('uk_results', '0016_auto_20160429_0938'),
    ]

    operations = [
        migrations.RunPython(add_party_colours),
    ]
