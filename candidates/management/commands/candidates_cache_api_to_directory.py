from __future__ import print_function, unicode_literals

import json
from datetime import datetime, timedelta
import os
from os.path import basename, exists, isdir, join
import re
from shutil import rmtree

from django.core.management.base import BaseCommand
from django.test import Client
from django.utils.six.moves.urllib_parse import urlsplit, parse_qs

from mysite.helpers import mkdir_p


def hostname_and_secure(url):
    split_url = urlsplit(url)
    return (split_url.netloc, split_url.scheme == 'https')


def path_and_query(url):
    split_url = urlsplit(url)
    return split_url.path + '?' + split_url.query


def page_from_url(url):
    page_values = parse_qs(urlsplit(url).query).get('page')
    if page_values:
        return int(page_values[0])
    return 1


def page_filename(endpoint, page_number):
    return '{0}-{1:06d}.json'.format(endpoint, page_number)


def update_latest_symlink(output_directory, subdirectory):
    tmp_symlink_location = join(output_directory, 'new')
    symlink_location = join(output_directory, 'latest')
    if exists(tmp_symlink_location):
        os.remove(symlink_location)
    os.symlink(subdirectory, tmp_symlink_location)
    os.rename(tmp_symlink_location, symlink_location)


def is_timestamped_dir(directory):
    dir_basename = basename(directory)
    return isdir(directory) and \
        re.search(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', dir_basename)


def prune(output_directory):
    timestamped_directories_to_remove = set(sorted(
        e for e in os.listdir(output_directory)
        if is_timestamped_dir(join(output_directory, e))
    )[:-4]) # Make sure we always leave at least the last 4 directories
    latest_symlink = join(output_directory, 'latest')
    if exists(latest_symlink):
        current_timestamped_directory = os.readlink(latest_symlink)
        timestamped_directories_to_remove.discard(
            current_timestamped_directory)
    # Don't remove any directory dated in the last 36 hours:
    remove_before = datetime.now() - timedelta(hours=36)
    too_recent = set(
        e for e in timestamped_directories_to_remove
        if datetime.strptime(e, '%Y-%m-%dT%H:%M:%S') >= remove_before)
    for e in too_recent:
        timestamped_directories_to_remove.remove(e)
    # Now remove any of those directories that are left:
    for e in sorted(timestamped_directories_to_remove):
        rmtree(join(output_directory, e))


class Command(BaseCommand):

    help = "Cache the output of the persons and posts endpoints to a directory"

    endpoints = ('persons', 'posts')

    def add_arguments(self, parser):
        parser.add_argument(
            'OUTPUT-DIRECTORY',
            help='The directory to write output to')
        parser.add_argument(
            'DIRECTORY-URL',
            help='The URL which that directory will be served at')
        parser.add_argument(
            '--page-size',
            type=int,
            help='How many results should be output per file (max 200)'
        )
        parser.add_argument(
            '--prune',
            action='store_true',
            help=('Prune older timestamped directories (those over 36 hours '
                  'old, never deleting the latest successfully generated one '
                  'or any of the 4 most recent)')
        )

    def rewrite_link(self, endpoint, url):
        if not url:
            return None
        page = page_from_url(url)
        filename = page_filename(endpoint, page)
        return '{0}{1}/{2}'.format(self.directory_url, self.timestamp, filename)

    def get(self, url):
        kwargs = {'SERVER_NAME': self.hostname}
        if self.secure:
            kwargs['wsgi.url_scheme'] = 'https'
            kwargs['secure'] = True
        return self.client.get(url, **kwargs)

    def rewrite_next_and_previous_links(self, endpoint, data):
        data['next'] = self.rewrite_link(endpoint, data['next'])
        data['previous'] = self.rewrite_link(endpoint, data['previous'])

    def get_api_results_to_directory(self, endpoint, json_directory, page_size):
        url = '/api/v0.9/{endpoint}/?page_size={page_size}&format=json'.format(
            page_size=page_size, endpoint=endpoint)
        while url:
            page = page_from_url(url)
            output_filename = join(json_directory, page_filename(endpoint, page))
            response = self.get(url)
            if response.status_code != 200:
                msg = "Unexpected response {0} from {1}"
                raise Exception(msg.format(response.status_code, url))
            data = json.loads(response.content.decode('utf-8'))
            original_next_url = data['next']
            self.rewrite_next_and_previous_links(endpoint, data)
            with open(output_filename, 'w') as f:
                json.dump(data, f, indent=4, sort_keys=True)
            # Now make sure the next URL works with the test client:
            if original_next_url:
                url = path_and_query(original_next_url)
            else:
                url = None

    def handle(self, *args, **options):
        self.client = Client()
        self.directory_url = options['DIRECTORY-URL']
        if not self.directory_url.endswith('/'):
            self.directory_url = self.directory_url + '/'
        self.hostname, self.secure = hostname_and_secure(self.directory_url)
        mkdir_p(options['OUTPUT-DIRECTORY'])
        self.timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        json_directory = join(options['OUTPUT-DIRECTORY'], self.timestamp)
        mkdir_p(json_directory)
        page_size = options['page_size']
        if not page_size:
            page_size = 200
        for endpoint in self.endpoints:
            self.get_api_results_to_directory(endpoint, json_directory, page_size)
        update_latest_symlink(options['OUTPUT-DIRECTORY'], self.timestamp)
        if options['prune']:
            prune(options['OUTPUT-DIRECTORY'])
