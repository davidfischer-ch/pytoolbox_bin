#! /usr/bin/env python
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

import glob, os, pyexiv2, shutil, stat
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from codecs import open
from os.path import abspath, basename, dirname, exists, expanduser, join, relpath
from pytoolbox.console import print_error
from pytoolbox.encoding import configure_unicode, to_bytes
from pytoolbox.filesystem import chown, try_makedirs
from pytoolbox.subprocess import cmd, rsync

from .lib import (
    find_albums, find_print_pictures, get_album_metadatas, get_picture_thumbnail, get_picture_uuid,
    parse_picture_uuid, PRINT_PATH, THUMB_PATH, UUID_TAG
)

from ..common import etc_path


def export_albums():
    u"""Generate or update albums metadatas file metadata.yml (e.g. set UUID)."""

    configure_unicode()
    HELP_PATH = u'Pictures base path'
    HELP_DEST = u'Pictures destination path'
    HELP_SIZE = u'Pictures thumbnails size'

    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter, epilog=export_albums.__doc__)
    parser.add_argument(u'path', help=HELP_PATH, default=None)
    parser.add_argument(u'dest', help=HELP_DEST, default=None)
    parser.add_argument(u'-s', u'--size', help=HELP_SIZE, nargs=2, type=int, default=(512, 512))
    args = parser.parse_args()

    pictures_path = abspath(expanduser(args.path))
    destination_path = abspath(expanduser(args.dest))
    for album_path in find_albums(pictures_path):
        print_src_path = join(album_path, PRINT_PATH)
        album_dst_path = join(destination_path, relpath(album_path, pictures_path))
        print_dst_path = join(album_dst_path, PRINT_PATH)
        thumb_dst_path = join(album_dst_path, THUMB_PATH)
        if not exists(thumb_dst_path):
            os.makedirs(thumb_dst_path)
        print(u'Synchronize album (rsync) to {0}'.format(print_dst_path))
        result = rsync(print_src_path, print_dst_path, makedest=True, archive=True, delete=True,
                       exclude_vcs=True, progress=True, recursive=True, fail=False)
        if result[u'returncode'] != 0:
            raise IOError(to_bytes(u'Failed to synchronize album {0}\nResult: {1}'.format(print_dst_path, result)))
        for print_picture_path in glob.glob(join(print_dst_path, u'*.jpg')):
            thumb_picture_path = join(thumb_dst_path, basename(print_picture_path))
            print(u'Create thumbnail {0}'.format(thumb_picture_path))
            thumbnail = get_picture_thumbnail(print_picture_path, args.size)
            thumbnail.save(thumb_picture_path)
        break


def generate_albums_metadatas():
    u"""
    Generate or update albums and pictures metadatas.

    For the album, this is metadata.yml (e.g. set UUID), and for the pictures, this is a unique identifier (UUID) set
    into pictures metadata (EXIFv2).

    """
    configure_unicode()
    HELP_FORCE = u'Force overwrite of any already existing metadatas'
    HELP_PATH = u'Pictures base path'

    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter, epilog=generate_albums_metadatas.__doc__)
    parser.add_argument(u'-f', u'--force', help=HELP_FORCE, action=u'store_true')
    parser.add_argument(u'path', help=HELP_PATH, default=None)
    args = parser.parse_args()

    print(u'Generate or update pictures metadatas')
    count = 0
    pictures_uuids = {}
    pictures_path = os.path.abspath(os.path.expanduser(args.path))
    for (raw_path, hugin_path, print_picture_path) in find_print_pictures(pictures_path, u'*.jpg'):
        count += 1
        metadatas = pyexiv2.ImageMetadata(print_picture_path)
        metadatas.read()  # FIXME IOError The file contains data of an unknown image type
        # Add a UUID if force is True or if picture's UUID tag is invalid or not set
        if args.force:
            metadatas[UUID_TAG] = get_picture_uuid(raw_path, hugin_path, print_picture_path, metadatas)
            metadatas.write()
        else:
            try:
                if parse_picture_uuid(metadatas.get(UUID_TAG).value) is None:
                    raise ValueError(to_bytes(u'Not a valid picture unique identifier'))
            except:
                metadatas[UUID_TAG] = get_picture_uuid(raw_path, hugin_path, print_picture_path, metadatas)
                metadatas.write()
        uuid_tag = metadatas[UUID_TAG].value
        try:
            pictures_uuids[uuid_tag].append(print_picture_path)
        except:
            pictures_uuids[uuid_tag] = [print_picture_path]
        total = len(pictures_uuids)
        print(u'Total:{0} Double:{1} {2} {3}'.format(total, count - total, uuid_tag, print_picture_path))

    print(u'Generate or update albums metadatas')
    # FIXME update according to filesystem stat of album directory / sub-directories (st_mtime) ?
    # Album stat posix.stat_result(st_mode=16893, st_ino=14094075, st_dev=35L, st_nlink=1,
    # st_uid=1000, st_gid=1000, st_size=35352, st_atime=1370328808, => st_mtime=1370328805 <=,
    # st_ctime=1370328805)
    pictures_path = os.path.abspath(os.path.expanduser(args.path))
    for album_path in find_albums(pictures_path):
        metadatas_path, metadatas = get_album_metadatas(album_path, save=True, update=True)
        print(u'Album found {0} with metadatas {1}'.format(album_path, metadatas))


def mount_photos_svn():
    u"""Install and configure davfs2 to mount the subversion repository of our family's pictures."""

    configure_unicode()
    FSTAB = u'/etc/fstab'
    CONFIGS = (
        (etc_path(u'davdfs2.conf'), u'/etc/davfs2/davfs2.conf'),
        (etc_path(u'server.pem'), u'/etc/davfs2/certs/server.pem')
    )
    SECRETS = abspath(expanduser(u'~/.davfs2/secrets'))

    HELP_URL, DEFAULT_URL = u'Pictures repository', u'https://claire-et-david.dyndns.org/nous/Photos'
    HELP_PATH, DEFAULT_PATH = u'Mount point', abspath(expanduser(u'~/PhotosSVN'))

    if not os.geteuid() == 0:
        print_error(u'Only root can run this script.')

    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter, epilog=mount_photos_svn.__doc__)
    parser.add_argument(u'login',    action=u'store')
    parser.add_argument(u'password', action=u'store')
    parser.add_argument(u'-u', u'--url',  action=u'store', help=HELP_URL,  default=DEFAULT_URL)
    parser.add_argument(u'-p', u'--path', action=u'store', help=HELP_PATH, default=DEFAULT_PATH)
    args = parser.parse_args()
    user = group = os.getlogin()

    print(u'Install and configure davfs2')
    cmd(u'apt-get install davfs2')
    cmd(u'usermod -aG davfs2 {0}'.format(user))
    os.chmod(u'/sbin/mount.davfs', 04755)

    print(u'Update {0}'.format(FSTAB))
    lines = filter(lambda l: args.url not in l, open(FSTAB, u'r', u'utf-8'))
    lines += u'{0} {1} davfs defaults,user,uid={2},gid=davfs2 0 0\n'.format(args.url, args.path, user)
    open(FSTAB, u'w', u'utf-8').write(u''.join(lines))

    for config in CONFIGS:
        print(u'Copy {0} to {1}'.format(config[0], config[1]))
        shutil.copyfile(config[0], config[1])

    print(u'Create {0}'.format(SECRETS))
    try_makedirs(dirname(SECRETS))
    with open(SECRETS, u'w', u'utf-8') as secrets_file:
        secrets_file.write(u'{0} {1} {2}'.format(args.url, args.login, args.password))
    os.chmod(SECRETS, stat.S_IRUSR)
    chown(dirname(SECRETS), user, group, recursive=True)

    print(u'Create {0}'.format(args.path))
    if not args.path in cmd(u'mount')['stdout']:
        # cmd(u'su {0} -c umount {1}'.format(user, args.path))
        try_makedirs(args.path)
        chown(dirname(args.path), user, group, recursive=True)
        # cmd(u'su {0} -c mount {1}'.format(user, args.path))
