from __future__ import unicode_literals

import hashlib
from tempfile import NamedTemporaryFile

from django.utils.translation import ugettext_lazy as _

from PIL import Image as PillowImage
import requests


def get_file_md5sum(filename):
    with open(filename, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


PILLOW_FORMAT_EXTENSIONS = {
    'JPEG': 'jpg',
    'MPO': 'jpg',
    'PNG': 'png',
    'GIF': 'gif',
    'BMP': 'bmp',
}


def get_image_extension(image_filename):
    with open(image_filename, 'rb') as f:
        try:
            pillow_image = PillowImage.open(f)
        except IOError as e:
            if 'cannot identify image file' in e.args[0]:
                print("Ignoring a non-image file {0}".format(
                    image_filename
                ))
                return None
            raise
        return PILLOW_FORMAT_EXTENSIONS[pillow_image.format]


class ImageDownloadException(Exception):
    pass


def download_image_from_url(image_url, max_size_bytes=(50 * 2**20)):
    """This downloads an image to a temporary file and returns the filename

    It raises an ImageDownloadException if a GET for the URL results
    in a HTTP response with status code other than 200, or the
    downloaded resource doesn't seem to be an image. It's the
    responsibility of the caller to delete the image once they're
    finished with it.  If the download exceeds max_size_bytes (default
    50MB) then this will also throw an ImageDownloadException."""
    with NamedTemporaryFile(delete=False) as image_ntf:
        image_response = requests.get(image_url, stream=True)
        if image_response.status_code != 200:
            msg = _("  Ignoring an image URL with non-200 status code "
                    "({status_code}): {url}")
            raise ImageDownloadException(
                msg.format(status_code=image_response.status_code, url=image_url))
        # Download no more than a megabyte at a time:
        downloaded_so_far = 0
        for chunk in image_response.iter_content(chunk_size=(2*20)):
            downloaded_so_far += len(chunk)
            if downloaded_so_far > max_size_bytes:
                raise ImageDownloadException(
                    _("The image exceeded the maximum allowed size"))
            image_ntf.write(chunk)
    # Trying to get the image extension checks that this really is
    # an image:
    if get_image_extension(image_ntf.name) is None:
        msg = _("  The image at {url} wasn't of a known type")
        raise ImageDownloadException(msg.format(url=image_url))
    return image_ntf.name
