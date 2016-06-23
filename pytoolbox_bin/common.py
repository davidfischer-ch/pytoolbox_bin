# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys


def config_path(*args):
    return os.path.join(os.path.expanduser('~/.pytoolbox_bin'), *args)


def error(msg, exit_code=None):
    print(msg, file=sys.stderr)
    if exit_code is not None:
        sys.exit(exit_code)
