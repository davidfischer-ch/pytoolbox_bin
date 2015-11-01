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

import argparse, multiprocessing, os

import github3
from pytoolbox.encoding import configure_unicode
from pytoolbox.filesystem import try_makedirs, try_remove
from pytoolbox.subprocess import git_clone_or_pull


def clone_it(directory, name, repository):
    directory = os.path.join(directory, name)
    print('Cloning/updating repository {0.full_name}'.format(repository))
    try:
        git_clone_or_pull(directory, repository.clone_url)
    except KeyboardInterrupt:
        try_remove(directory, recursive=True)


def clone_starred():
    """Iterate over repositories starred by someone and clone them."""

    configure_unicode()
    DEFAULT_OUTPUT = os.path.abspath(os.path.expanduser('~/github/stars'))
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     epilog=clone_starred.__doc__)
    parser.add_argument('username',          help='Name of user whose stars you want to clone')
    parser.add_argument('-o', '--output',    help='Clones directory',    default=DEFAULT_OUTPUT)
    parser.add_argument('-p', '--processes', help='Number of processes', type=int, default=min(4, os.cpu_count() * 2))
    parser.add_argument('-d', '--delete', action='store_true', help='Remove clones of unstarred repositories')
    args = parser.parse_args()

    output = os.path.abspath(os.path.expanduser(args.output))
    try_makedirs(output)

    starred_repositories = {r.name: r for r in github3.starred_by(args.username)}

    if args.delete:
        for name in os.listdir(output):
            if not name in starred_repositories:
                print('Remove clone of unstarred repository {0}'.format(name))
                try_remove(os.path.join(output, name), recursive=True)

    pool = multiprocessing.Pool(processes=args.processes)
    for name, repository in starred_repositories.iteritems():
        pool.apply_async(clone_it, args=(output, name, repository))
    pool.close()
    pool.join()
    print('Work done!')
