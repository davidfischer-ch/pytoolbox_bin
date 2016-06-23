#! /usr/bin/env python
# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals


def main():
    from pytoolbox.unittest import runtests
    return runtests(__file__, cover_packages=[u'pytoolbox_bin'], packages=[u'pytoolbox_bin'])

if __name__ == u'__main__':
    main()
