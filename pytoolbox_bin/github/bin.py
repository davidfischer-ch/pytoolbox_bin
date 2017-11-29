# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse, multiprocessing, os, re

import github3
from pytoolbox.encoding import configure_unicode
from pytoolbox.filesystem import try_makedirs, try_remove
from pytoolbox.subprocess import cmd, git_clone_or_pull


def clone_it(repository):
    print('Cloning/updating repository {0.full_name}'.format(repository))
    try:
        git_clone_or_pull(repository.directory, repository.clone_url)
    except KeyboardInterrupt:
        try_remove(repository.directory, recursive=True)


def has_contributed_to(repository, strings):
    """Iterate over local repositories and count commits from given author."""
    log = cmd(['git', 'log'], cwd=repository.directory)['stdout']
    return bool(re.search('|'.join(strings).encode('utf-8'), log))


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

    me = ['davidfischer-ch', 'David Fischer', 'david.fischer.ch@gmail.com']
    output = os.path.abspath(os.path.expanduser(args.output))
    try_makedirs(output)

    def add_directory(repository):
        repository.directory = os.path.join(output, repository.full_name)
        return repository

    starred_repositories = {r.full_name: add_directory(r) for r in github3.starred_by(args.username)}

    if args.delete:
        for dirpath, dirnames, filenames in os.walk(output):
            full_name = os.path.relpath(dirpath, output)
            if full_name.count(os.path.sep) == 1:
                if not full_name in starred_repositories:
                    print('Remove clone of unstarred repository {0}'.format(full_name))
                    try_remove(os.path.join(output, full_name), recursive=True)
                dirnames.clear()

    contributed_repositories = [r for r in starred_repositories.itervalues() if has_contributed_to(r, me)]
    print(os.linesep.join(sorted(r.full_name for r in contributed_repositories)))
    print('You contributed to {0} of the {1} repositories you starred!'.format(
        len(contributed_repositories), len(starred_repositories)
    ))

    return
    pool = multiprocessing.Pool(processes=args.processes)
    pool.map_async(clone_it, starred_repositories.itervalues())
    pool.close()
    pool.join()

    print('Job done!')
