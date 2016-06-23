# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse, multiprocessing, os

import github3
from pytoolbox.encoding import configure_unicode
from pytoolbox.filesystem import try_makedirs, try_remove
from pytoolbox.subprocess import git_clone_or_pull


def clone_it(directory, repository):
    print('Cloning/updating repository {0.full_name}'.format(repository))
    directory = os.path.join(directory, repository.full_name)
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

    starred_repositories = {r.full_name: r for r in github3.starred_by(args.username)}

    if args.delete:
        for dirpath, dirnames, filenames in os.walk(output):
            full_name = os.path.relpath(dirpath, output)
            if full_name.count(os.path.sep) == 1:
                if not full_name in starred_repositories:
                    print('Remove clone of unstarred repository {0}'.format(full_name))
                    try_remove(os.path.join(output, full_name), recursive=True)
                dirnames.clear()

    pool = multiprocessing.Pool(processes=args.processes)
    for repository in starred_repositories.itervalues():
        pool.apply_async(clone_it, args=(output, repository))
    pool.close()
    pool.join()

    print('Job done!')
