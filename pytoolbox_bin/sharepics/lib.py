# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                    PYTOOLBOX BIN - PERSONAL UTILITY SCRIPTS BASED ON PYTOOLBOX AND OTHER GOODIES
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2013 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's pytoolbox_bin Project.
#
# This project is free software: you can redistribute it and/or modify it under the terms of the EUPL v. 1.1 as provided
# by the European Commission. This project is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See the European Union Public License for more details.
#
# You should have received a copy of the EUPL General Public License along with this project.
# If not, see he EUPL licence v1.1 is available in 22 languages:
#     22-07-2013, <https://joinup.ec.europa.eu/software/page/eupl/licence-eupl>
#
# Retrieved from https://github.com/davidfischer-ch/pytoolbox_bin.git

from __future__ import absolute_import, division, print_function, unicode_literals

import datetime, fnmatch, glob, itertools, os, re, uuid, yaml
from codecs import open
from os.path import basename, dirname, exists, getmtime, join, splitext
from PIL import Image
from pytoolbox.crypto import githash
from pytoolbox.datetime import datetime_now, datetime2str
from pytoolbox.encoding import string_types
from pytoolbox.validation import valid_uuid


HUGIN_PATH, PRINT_PATH, THUMB_PATH, RAW_PATH = u'hugin', u'print', u'thumb-border', u'raw'
HUGIN_EXTENSIONS, RAW_EXTENSIONS = (u'.pto'), (u'.CR2', u'.CRW', u'.jpg')
METADATAS_FILE = u'metadata.yml'
NAME_REGEX = re.compile(ur'(.+)_(\d+)')
UUID_REGEX = re.compile(
    ur'(?P<raw_uuid>[0-9a-z]{40});(?P<number>[1-9]*[0-9]+);(?P<random_part>[0-9a-z]{8})')

UUID_TAG = u'Exif.Image.ImageDescription'


def find_albums(directory):
    u"""
    Find and return path to albums that are stored in any sub-directory of ``directory``.
    An album is a directory containing a ``print/`` sub-directory.

    :param directory: Pictures root directory
    :type directory: :class:`str`

    **Example usage**

    >>> import tempfile
    >>> temp = tempfile.mkdtemp()
    >>> os.chdir(temp)
    >>> os.makedirs(u'Album 1/print')
    >>> os.makedirs(u'Album 2/print')
    >>> os.makedirs(u'sub-dir/Album 3/print')
    >>> os.makedirs(u'sub-dir/Not an album/raw')
    >>> os.makedirs(u'Album 1/raw')
    >>> albums = [a for a in find_albums(temp)]
    >>> assert(len(albums) == 3)
    >>> assert(os.path.join(temp, u'Album 1') in albums)
    >>> assert(os.path.join(temp, u'Album 2') in albums)
    >>> assert(os.path.join(temp, u'sub-dir/Album 3') in albums)
    """
    for root, dirnames, filenames in os.walk(directory):
        if os.path.basename(root) == PRINT_PATH:
            yield os.path.dirname(root)


def find_print_pictures(directory, pattern):
    u"""
    Find and return path to pictures matching ``pattern`` that are stored in any ``print/``
    sub-directory of ``directory``.

    :param directory: Pictures root directory
    :type directory: :class:`str`
    :param pattern: Filename matching pattern
    :type pattern: :class:`str`

    **Example usage**

    >>> import tempfile
    >>> temp = tempfile.mkdtemp()
    >>> os.chdir(temp)
    >>> os.makedirs(u'Album 1/print')
    >>> os.makedirs(u'Album 2/print')
    >>> os.makedirs(u'Album 1/raw')
    >>> f = open(u'Album 1/print/1a.jpg', u'w', u'utf-8')
    >>> f = open(u'Album 1/print/1b.jpg', u'w', u'utf-8')
    >>> f = open(u'Album 2/print/2a.jpg', u'w', u'utf-8')
    >>> f = open(u'Album 2/print/2b.mp4', u'w', u'utf-8')
    >>> f = open(u'Album 2/print/2c.JPG', u'w', u'utf-8')
    >>> f = open(u'Album 1/raw/1r.jpg', u'w', u'utf-8')
    >>> pics = [p for (r, h, p) in find_print_pictures(temp, u'*.jpg')]
    >>> assert(len(pics) == 3)
    >>> assert(os.path.join(temp, u'Album 1/print/1a.jpg') in pics)
    >>> assert(os.path.join(temp, u'Album 1/print/1b.jpg') in pics)
    >>> assert(os.path.join(temp, u'Album 2/print/2a.jpg') in pics)
    """
    for print_path, dirnames, filenames in os.walk(directory):
        if basename(print_path) == PRINT_PATH:
            raw_path = join(dirname(print_path), RAW_PATH)
            if not exists(raw_path):
                raw_path = None
            hugin_path = join(dirname(print_path), HUGIN_PATH)
            if not exists(hugin_path):
                hugin_path = None
            for print_picture_path in fnmatch.filter(filenames, pattern):
                yield (raw_path, hugin_path, join(print_path, print_picture_path))


def get_album_metadatas(album_path, update=False, save=False):
    u"""
    Returns loaded metadatas yaml file of an album, fall-back to a default value.

    The content is loaded field by field and any invalid field is replaced by a default value.

    :param update: Set last_update_at to 'now' if set to True
    :type update: bool

    :param save: Save-back albums metadatas to metadatas yaml file if set to True.
    :type save: bool

    **Example usage**:

    >>> import time
    >>> from nose.tools import assert_equal
    >>> path, metadatas = get_album_metadatas(u'do_not_exist')
    >>> assert(isinstance(metadatas, dict))
    >>> print(path, metadatas[u'rights'], metadatas[u'description'])
    do_not_exist/metadata.yml [] None
    >>> assert(valid_uuid(metadatas[u'uuid'], False))

    >>> with open(u'metadata.yml', u'w', u'utf-8') as f:
    ...     m = {u'bad_field': 10, u'uuid': u'1234', u'rights': [u'nous'], u'description': u'some text'}
    ...     yaml.dump(m, f)
    >>> path, metadatas = get_album_metadatas(u'.', save=True)
    >>> expected = dict(**metadatas)
    >>> expected.update({u'rights': [u'nous'], u'description': u'some text'})
    >>> assert_equal(metadatas, expected)

    >>> with open(u'salut', u'w', u'utf-8') as f:
    ...     f.write(u'toi')
    >>> time.sleep(1.1)
    >>> path, metadatas = get_album_metadatas(u'.', update=True)
    >>> assert(expected[u'last_update_at'] != metadatas[u'last_update_at'])
    >>> os.remove(u'metadata.yml')
    """
    metadatas_path = os.path.join(album_path, METADATAS_FILE)
    print_path = join(album_path, PRINT_PATH)
    try:
        t = datetime2str(datetime.datetime.fromtimestamp(getmtime(print_path)), append_utc=True)
    except OSError:
        t = datetime_now(append_utc=True)
    metadatas = {u'uuid': str(uuid.uuid4()), u'rights': [], u'description': None, u'last_update_at': t}
    if exists(metadatas_path):
        with open(metadatas_path, u'r', u'utf-8') as f:
            data = yaml.load(f)
            if valid_uuid(data.get(u'uuid'), False):
                metadatas[u'uuid'] = data[u'uuid']
            if isinstance(data.get(u'rights'), list):
                metadatas[u'rights'] = data[u'rights']
            if isinstance(data.get(u'description'), string_types):
                metadatas[u'description'] = data[u'description']
            if isinstance(data.get(u'last_update_at'), string_types) and not update:
                metadatas[u'last_update_at'] = data[u'last_update_at']
    if save:
        with open(metadatas_path, u'w', u'utf-8') as f:
            yaml.dump(metadatas, f)
    return (metadatas_path, metadatas)


def get_picture_uuid(raw_path, hugin_path, print_picture_path, metadatas):
    u"""
    Returns computed unique identifier for a picture.

    The pattern of this identifier is ``raw_githash;number;random_part``.

    The ``raw_githash`` will be the githash() of a chosen file, in that order:

    * The source raw picture if found in ``raw_path``.
    * The hugin projet if found in ``hugin_path``.
    * Defaults to the githash() of the print picture itself.

    The ``number`` is a numeric value extracted from picture's filename.

    The ``random_part`` is set to a random value (8 characters) and this part of the identifier
    ensure that generated picture's uuid is as unique as it should be. For example one can produce
    more than 1 print picture from a raw picture (B&W, zoom, ...).

    .. warning::

        FIXME detection of duplicate print-only pictures is made impossible by metadatas update !
    """
    random_part = str(uuid.uuid4())[:8]  # FIXME this is not the best way to get a 8 bytes random
    print_picture_name, number = (splitext(basename(print_picture_path))[0], 0)
    match = NAME_REGEX.match(print_picture_name)
    if match:
        print_picture_name, number = match.groups()
    if raw_path is not None:
        raw_picture_filter = join(raw_path, print_picture_name)
        for extension in RAW_EXTENSIONS:
            paths = glob.glob(raw_picture_filter + extension)
            if len(paths) == 1:
                with open(paths[0], u'r', u'utf-8') as raw_picture:
                    return u'{0};{1};{2}'.format(githash(raw_picture.read()), number, random_part)
    if hugin_path is not None:
        hugin_project_filter = join(hugin_path, print_picture_name)
        for extension in HUGIN_EXTENSIONS:
            paths = glob.glob(hugin_project_filter + extension)
            if len(paths) == 1:
                with open(paths[0], u'r', u'utf-8') as hugin_project:
                    return u'{0};{1};{2}'.format(githash(hugin_project.read()), number, random_part)
    with open(print_picture_path, u'r', u'utf-8') as print_picture:
        return u'{0};{1};{2}'.format(githash(print_picture.read()), number, random_part)


def get_picture_thumbnail(picture_path, size, background=0x000000):
    image = Image.open(picture_path)
    image.thumbnail(size, Image.ANTIALIAS)
    thumbnail = Image.new(image.mode, size, background)
    delta = tuple((t - i)/2 for t, i in itertools.izip(thumbnail.size, image.size))
    thumbnail.paste(image, delta)
    return thumbnail


def parse_picture_uuid(uuid_str):
    u"""
    Returns a dictionary containing the components of a picture ``uuid_str`` string.

    The pattern of this identifier is ``raw_githash;number;random_part``.

    **Example usage**:

    >>> from nose.tools import assert_equal
    >>> assert(parse_picture_uuid(u'Tabby') is None)
    >>> expected = {u'number': u'2', u'random_part': u'a3b9c4ee', u'raw_uuid': u'b699be2542f21c722a4e4777632064f30966ed4e'}
    >>> assert_equal(parse_picture_uuid(githash(u'Tabby') + u';2;a3b9c4ee'), expected)
    """
    match = UUID_REGEX.match(uuid_str)
    if match:
        return match.groupdict()
    return None
