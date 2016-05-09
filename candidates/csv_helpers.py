from __future__ import unicode_literals

from compat import BufferDictWriter
from .models import CSV_ROW_FIELDS


def _candidate_sort_by_name_key(row):
    return (
        row['name'].split()[-1],
        row['name'].rsplit(None, 1)[0],
        not row['election_current'],
        row['election_date'],
        row['election'],
        row['post_label']
    )

def _candidate_sort_by_post_key(row):
    return (
        not row['election_current'],
        row['election_date'],
        row['election'],
        row['post_label'],
        row['name'].split()[-1],
        row['name'].rsplit(None, 1)[0],
    )


def list_to_csv(candidates_list, group_by_post=False):
    from .election_specific import EXTRA_CSV_ROW_FIELDS
    csv_fields = CSV_ROW_FIELDS + EXTRA_CSV_ROW_FIELDS
    writer = BufferDictWriter(fieldnames=csv_fields)
    writer.writeheader()
    if group_by_post:
        sorted_rows = sorted(candidates_list, key=_candidate_sort_by_post_key)
    else:
        sorted_rows = sorted(candidates_list, key=_candidate_sort_by_name_key)
    for row in sorted_rows:
        writer.writerow(row)
    return writer.output
