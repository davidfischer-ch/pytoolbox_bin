# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse

from pytoolbox import virtualenv


def relocate():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     epilog=virtualenv.relocate.__doc__)
    parser.add_argument('source_directory')
    parser.add_argument('destination_directory')
    args = parser.parse_args()
    virtualenv.relocate(args.source_directory, args.destination_directory)
