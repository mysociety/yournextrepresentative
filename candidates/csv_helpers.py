import csv
import StringIO

from .models import CSV_ROW_FIELDS


def list_to_csv(candidates_list):
    output = StringIO.StringIO()
    writer = csv.writer(output, dialect=csv.excel)
    writer.writerow(CSV_ROW_FIELDS)
    for row in candidates_list:
        writer.writerow(row)
    return output.getvalue()
