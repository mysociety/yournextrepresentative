import csv
from io import StringIO

from .models import CSV_ROW_FIELDS

def encode_row_values(d):
    return {
        k: unicode('' if v is None else v).encode('utf-8')
        for k, v in d.items()
    }

def candidate_sort_key(row):
    return (row['election'], row['post_label'], row['name'].split()[-1])

def list_to_csv(candidates_list):
    from .election_specific import EXTRA_CSV_ROW_FIELDS
    csv_fields = CSV_ROW_FIELDS + EXTRA_CSV_ROW_FIELDS
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=csv_fields,
        dialect=csv.excel)
    writer.writeheader()
    for row in sorted(candidates_list, key=candidate_sort_key):
        writer.writerow(encode_row_values(row))
    return output.getvalue()
