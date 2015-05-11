# -*- coding: utf-8 -*-

from datetime import date

ELECTIONS = {
    # Party primaries for deputies.

    # For this and the next two elections in this module, we don't want to
    # create an organization membership on winning the election, since these
    # should only be set for the winner of the actual election, not the winner
    # of the primary. For future reference, I'm keeping the suggested
    # organization IDs and names in the comments though:
    #  'organization_id': 'hcdn',
    #  'organization_name': 'Cámara de Diputados',
    'diputados-argentina-paso-2015': {
        'for_post_role': 'Candidato a Diputado Nacional',
        'election_date': date(2015, 8, 9),
        'candidacy_start_date': date(2015, 6, 22),
        'name': ' Diputados Nacionales PASO 2015',
        'current': True,
        'use_for_candidate_suggestions': False,
        'party_membership_start_date': date(2015, 6, 22),
        'party_membership_end_date': date(9999, 12, 31),
    },
    # Party primaries for governors of provinces
    #  'organization_id': 'gobernador',
    #  'organization_name': 'Gobernador',
    'gobernadores-argentina-paso-2015': {
        'for_post_role': 'Candidato a Gobernador',
        'election_date': date(2015, 8, 9),
        'candidacy_start_date': date(2015, 6, 22),
        'name': 'Gobernador PASO 2015',
        'current': True,
        'party_membership_start_date': date(2015, 6, 22),
        'party_membership_end_date': date(9999, 12, 31),
    },
    #  'organization_id': 'hcsn',
    #  'organization_name': 'Senado de la Nación',
    'senadores-argentina-paso-2015': {
        'for_post_role': 'Candidato a Senador Nacional',
        'election_date': date(2015, 8, 9),
        'candidacy_start_date': date(2015, 6, 22),
        'name': 'Senadores Nacionales PASO 2015',
        'current': True,
        'party_membership_start_date': date(2015, 6, 22),
        'party_membership_end_date': date(9999, 12, 31),
    },
    # Presidential candidates
    'presidentes-argentina-paso-2015': {
        'for_post_role': 'Candidato a Presidente',
        'election_date': date(2015, 8, 9),
        'candidacy_start_date': date(2015, 6, 22),
        'organization_id': 'pen',
        'organization_name': 'Presidencia de la Nación Argentina',
        'name': 'Presidentes PASO 2015',
        'current': True,
        'party_membership_start_date': date(2015, 6, 22),
        'party_membership_end_date': date(9999, 12, 31),
    },
}
