from __future__ import unicode_literals
import six

import csv
import io

from .models import CSV_ROW_FIELDS


class StreamDictWriter(object):

    def __init__(self, fieldnames):
        self.f = io.BytesIO() if six.PY2 else io.StringIO()
        self.writer = self._DictWriter(self.f, fieldnames, dialect=csv.excel)

        self.writeheader = self.writer.writeheader
        self.writerow = self.writer.writerow
        self.writerows = self.writer.writerows

    @property
    def output(self):
        output = self.f.getvalue()
        if six.PY2:
            output = output.decode('utf-8')
        return output

    class _DictWriter(csv.DictWriter):

        def _dict_to_list(self, rowdict):
            # py2 csv uses old-style classes, so we can't do `super()`
            rowlist = csv.DictWriter._dict_to_list(self, rowdict)
            if six.PY2:
                rowlist = [unicode('' if i is None else i).encode('utf-8')
                           for i in rowlist]
            return rowlist


def candidate_sort_key(row):
    return (row['election'], row['post_label'], row['name'].split()[-1])


def list_to_csv(candidates_list):
    from .election_specific import EXTRA_CSV_ROW_FIELDS
    csv_fields = CSV_ROW_FIELDS + EXTRA_CSV_ROW_FIELDS
    writer = StreamDictWriter(fieldnames=csv_fields)
    writer.writeheader()
    for row in sorted(candidates_list, key=candidate_sort_key):
        writer.writerow(row)
    return writer.output
