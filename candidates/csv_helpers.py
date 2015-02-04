import csv
import StringIO

from .models import CSV_ROW_FIELDS

def encode_row_values(d):
    return {
        k: unicode('' if v is None else v).encode('utf-8')
        for k, v in d.items()
    }

def list_to_csv(candidates_list):
    output = StringIO.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=CSV_ROW_FIELDS,
        dialect=csv.excel)
    writer.writeheader()
    for row in candidates_list:
        writer.writerow(encode_row_values(row))
    return output.getvalue()
