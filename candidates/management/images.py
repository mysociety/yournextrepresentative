from __future__ import unicode_literals

import hashlib

from PIL import Image as PillowImage


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
