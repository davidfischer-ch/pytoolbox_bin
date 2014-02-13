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

import os, shutil
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from github3 import iter_starred
from os.path import abspath, exists, expanduser, join
from pytoolbox.encoding import configure_unicode
from pytoolbox.filesystem import try_makedirs
from pytoolbox.subprocess import cmd


def clone_starred():
    u"""Iterate over repositories starred by someone and clone them."""

    configure_unicode()
    HELP_DELETE = u'Remove clones of unstarred repositories'
    HELP_FETCH = u'Fetch already-cloned repositories'
    HELP_OUTPUT = u'Clones directory'
    HELP_USERNAME = u'Name of user whose stars you want to clone'
    DEFAULT_OUTPUT = abspath(expanduser(u'~/github_starred'))

    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter, epilog=clone_starred.__doc__)
    parser.add_argument(u'username', action=u'store', help=HELP_USERNAME)
    parser.add_argument(u'-o', u'--output', action=u'store', help=HELP_OUTPUT, default=DEFAULT_OUTPUT)
    parser.add_argument(u'-d', u'--delete', action=u'store_true', help=HELP_DELETE, default=False)
    parser.add_argument(u'-c', u'--fetch', action=u'store_true', help=HELP_FETCH, default=False)
    args = parser.parse_args()

    output = abspath(expanduser(args.output))
    try_makedirs(output)

    starred_repositories = {r.name: r for r in iter_starred(args.username)}

    if args.delete:
        for name in os.listdir(output):
            if not name in starred_repositories:
                print(u'Remove clone of unstarred repository {0}'.format(name))
                shutil.rmtree(join(output, name))

    for name, repository in starred_repositories.iteritems():
        directory = join(output, name)
        if exists(directory):
            if args.fetch:
                print(u'Fetching already cloned repository {0}'.format(repository.full_name))
                cmd([u'git', u'fetch'], cwd=directory, log=print)
            else:
                print(u'Skip already cloned repository {0}'.format(repository.full_name))
        else:
            print(u'Cloning repository {0}'.format(repository.full_name))
            try:
                cmd([u'git', u'clone', repository.clone_url, directory], log=print)
            except KeyboardInterrupt:
                shutil.rmtree(directory, ignore_errors=True)
