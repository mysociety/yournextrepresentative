import csv
import StringIO

from .models import CSV_ROW_FIELDS


def list_to_csv(candidates_list):
    output = StringIO.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=CSV_ROW_FIELDS,
        dialect=csv.excel)
    writer.writeheader()
    for row in candidates_list:
        writer.writerow(row)
    return output.getvalue()
