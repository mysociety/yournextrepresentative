from __future__ import unicode_literals
import six

import csv
import io

from .models import CSV_ROW_FIELDS


class StreamDictReader(object):

    def __init__(self, content):
        self._reader = csv.DictReader(self._prepare(content))
        self.fieldnames = self._reader.fieldnames

    def __iter__(self): return self

    if six.PY2:
        def _prepare(self, content):
            if isinstance(content, unicode):
                content = content.encode('utf-8')
            return io.BytesIO(content)

        def __next__(self):
            next_ = next(self._reader)
            return {k.decode('utf-8'): v.decode('utf-8')
                    for k, v in next_.items()}
        next = __next__
    else:
        def _prepare(self, content):
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            return io.StringIO(content)

        def __next__(self): return next(self._reader)


class StreamDictWriter(object):

    def __init__(self, fieldnames):
        self._f = self._buffer()
        self._writer = self._writer_class(self._f, fieldnames,
                                          dialect=csv.excel)
        self.writeheader = self._writer.writeheader
        self.writerow = self._writer.writerow
        self.writerows = self._writer.writerows

    if six.PY2:
        @property
        def output(self): return self._f.getvalue().decode('utf-8')

        class _DictWriter(csv.DictWriter):

            def _dict_to_list(self, rowdict):
                # py2 csv uses old-style classes, so we can't do `super()`
                rowlist = csv.DictWriter._dict_to_list(self, rowdict)
                rowlist = [unicode('' if i is None else i).encode('utf-8')
                           for i in rowlist]
                return rowlist

        _buffer, _writer_class = io.BytesIO, _DictWriter
    else:
        @property
        def output(self): return self._f.getvalue()

        _buffer, _writer_class = io.StringIO, csv.DictWriter


def _candidate_sort_key(row):
    return (row['election'], row['post_label'], row['name'].split()[-1])


def list_to_csv(candidates_list):
    from .election_specific import EXTRA_CSV_ROW_FIELDS
    csv_fields = CSV_ROW_FIELDS + EXTRA_CSV_ROW_FIELDS
    writer = StreamDictWriter(fieldnames=csv_fields)
    writer.writeheader()
    for row in sorted(candidates_list, key=_candidate_sort_key):
        writer.writerow(row)
    return writer.output
