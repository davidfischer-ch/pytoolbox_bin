# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import os, re


class Like(object):

    FILENAME_REGEX = re.compile(r'(?P<directory>.+)%s(?P<title>[^%s]+)_(?P<id>.{11,})\.(?P<extension>\S{3})' % (
                                os.sep, os.sep))

    def __init__(self, id, title, directory, extension='mp4', thumbnail_url=None):
        self.id = id
        self.title = remove_special_chars(title)
        self.directory = directory
        self.extension = extension
        self.thumbnail_url = thumbnail_url

    @property
    def video(self):
        return '{0.directory}{1}{0.title}_{0.id}.{0.extension}'.format(self, os.sep)

    @property
    def thumbnail(self):
        return '{0.directory}{1}{0.title}_{0.id}.jpg'.format(self, os.sep)

    @classmethod
    def from_api_response(cls, response, directory):
        thumbnails = response['snippet'].get('thumbnails')
        return cls(id=response['id'], title=response['snippet']['title'], directory=directory,
                   thumbnail_url=thumbnails['high']['url'] if thumbnails else None)

    @property
    def deleted(self):
        return self.title == 'Deleted video'

    @classmethod
    def from_filename(cls, filename):
        try:
            return cls(**cls.FILENAME_REGEX.match(filename).groupdict())
        except AttributeError:
            return None


def remove_special_chars(filename):
    return (filename.replace('?', '').replace('"', '').replace('/', '-')
                    .replace('|', '-').replace(':', '-').replace('*', '-'))
