# -*- encoding: utf-8 -*-

#**********************************************************************************************************************#
#                    PYTOOLBOX BIN - PERSONAL UTILITY SCRIPTS BASED ON PYTOOLBOX AND OTHER GOODIES
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2012-2014 David Fischer. All rights reserved.
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
