from __future__ import print_function, unicode_literals

import errno
import hashlib
import magic
import mimetypes
import os
from os.path import dirname, join, exists
import requests

from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import FileSystemStorage

from official_documents.models import OfficialDocument
from elections.models import Election
from popolo.models import Post, Area

from compat import BufferDictReader

allowed_mime_types = set([
    b'application/pdf',
    b'application/msword',
    b'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
])

PDF_COLUMN_HEADERS_TO_TRY = (
    'Statement of Persons Nominated (SOPN) URL',
    'Link to PDF',
)

POST_OR_AREA_COLUMN_HEADERS_TO_TRY = (
    'Region',
    'Constituency',
    'Ward',
    'Area',
)

def download_file_cached(url):
    url_hash = hashlib.md5(url).hexdigest()
    directory = join(dirname(__file__), '.noms-cache')
    try:
        os.mkdir(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    filename = join(directory, url_hash)
    if exists(filename):
        return filename
    try:
        r = requests.get(url)
    except requests.exceptions.SSLError:
        print("Caught an SSLError, so retrying without certificate validation")
        r = requests.get(url, verify=False)
    with open(filename, 'w') as f:
        f.write(r.content)
    return filename


def get_column_header(possible_column_headers, row):
    return [
        ch for ch in possible_column_headers
        if ch in row
    ][0]


class Command(BaseCommand):
    help = "Import official documents for posts from a URL to a CSV file"

    args = "<CSV_URL>"

    def add_arguments(self, parser):
        parser.add_argument('--delete-existing', action='store_true')
        parser.add_argument('--election')

    def handle(self, *args, **options):

        csv_url, = args

        override_election = None
        override_election_slug = options['election']
        if override_election_slug:
            try:
                override_election = Election.objects.get(
                    slug=override_election_slug
                )
            except Election.DoesNotExist:
                msg = 'No election with slug {0} found'
                raise CommandError(msg.format(override_election_slug))

        election_name_to_election = {}

        mime_type_magic = magic.Magic(mime=True)
        storage = FileSystemStorage()

        r = requests.get(csv_url)
        r.encoding = 'utf-8'
        reader = BufferDictReader(r.text)
        for row in reader:
            post_or_area_header = get_column_header(
                POST_OR_AREA_COLUMN_HEADERS_TO_TRY, row
            )

            name = row[post_or_area_header]
            if not name:
                continue
            name = name.strip()

            # If there was no election specified, try to find it from
            # the 'Election' column (which has the election name):
            if override_election_slug:
                election = override_election
            else:
                if 'Election' not in row:
                    raise CommandError("There is no election name in the 'Election' column, so you must supply an election slug with --election")
                election_name = row['Election']
                election = election_name_to_election.get(election_name)
                if election is None:
                    election = Election.objects.get(slug=election_name)
                    election_name_to_election[election_name] = election

            try:
                post = Post.objects.get(
                    extra__slug=name,
                    extra__elections=election,
                )
            except Post.DoesNotExist:
                msg = "Failed to find the post {0}, guessing it might be the area name instead"
                # print(msg.format(name))
                # If the post name isn't there, try getting it from
                # the area:
                try:
                    area = Area.objects.get(name=name)
                except (Area.DoesNotExist, Area.MultipleObjectsReturned):
                    pass

                try:
                    post = Post.objects.get(label=name, extra__elections=election)
                    area = post.area
                except Post.DoesNotExist:
                    # print("Failed to find post with for {0}".format(name))
                    continue

            # Check that the post is actually valid for this election:
            if election not in post.extra.elections.all():
                msg = "The post {post} wasn't in the election {election}"
                raise CommandError(msg.format(post=post.label, election=election.name))

            document_url_column = get_column_header(PDF_COLUMN_HEADERS_TO_TRY, row)
            document_url = row[document_url_column]
            if not document_url:
                # print("No URL for {0}".format(name))
                continue
            existing_documents = OfficialDocument.objects.filter(
                document_type=OfficialDocument.NOMINATION_PAPER,
                post_id=post,
                election=election,
            )
            if existing_documents.count() > 0:
                if options['delete_existing']:
                    print("Removing existing documents")
                    existing_documents.delete()
                else:
                    msg = "Skipping {0} since it already had documents for {1}"
                    # print(msg.format(name, election))
                    continue
            try:
                downloaded_filename = download_file_cached(document_url)
            except requests.exceptions.ConnectionError:
                print("Connection failed for {0}".format(name))
                print("The URL was:", document_url)
                continue
            except requests.exceptions.MissingSchema:
                # This is probably someone putting notes in the URL
                # column, so ignore:
                print("Probably not a document URL for {0}: {1}".format(
                    name, document_url
                ))
                continue
            mime_type = mime_type_magic.from_file(downloaded_filename)
            extension = mimetypes.guess_extension(mime_type)
            if mime_type not in allowed_mime_types:
                print("Ignoring unknown MIME type {0} for {1}".format(
                    mime_type,
                    name,
                ))
                continue
            filename = "official_documents/{post_id}/statement-of-persons-nominated{extension}".format(
                post_id=post.extra.slug,
                extension=extension,
            )
            with open(downloaded_filename, 'rb') as f:
                storage_filename = storage.save(filename, f)

            OfficialDocument.objects.create(
                document_type=OfficialDocument.NOMINATION_PAPER,
                uploaded_file=storage_filename,
                election=election,
                post=post,
                source_url=document_url
            )
            message = "Successfully added the Statement of Persons Nominated for {0}"
            print(message.format(name))
