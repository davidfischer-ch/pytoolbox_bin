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

import sys
from codecs import open
from pip.req import parse_requirements
from setuptools import setup, find_packages

major, minor = sys.version_info[:2]
kwargs = {}
if major >= 3:
    print('Converting code to Python 3 helped by 2to3')
    kwargs['use_2to3'] = True

# https://pypi.python.org/pypi?%3Aaction=list_classifiers

classifiers = """
Development Status :: 2 - Pre-Alpha
Environment :: Console
Intended Audience :: Developers
Intended Audience :: End Users/Desktop
License :: OSI Approved :: European Union Public Licence 1.1 (EUPL 1.1)
Natural Language :: English
Operating System :: POSIX :: Linux
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Programming Language :: Python :: Implementation :: CPython
Topic :: Multimedia :: Sound/Audio
Topic :: Multimedia :: Video
Topic :: Utilities
"""

not_yet_tested = """
Programming Language :: Python :: 3
Programming Language :: Python :: 3.2
Programming Language :: Python :: 3.3
Operating System :: MacOS :: MacOS X
Operating System :: Unix
"""

packages = find_packages()
if 'tests' in packages:
    packages.remove('tests')

setup(name='pytoolbox_bin',
      version='0.2.2',
      packages=packages,
      description='Personal utility scripts based on pytoolbox and other goodies.',
      long_description=open('README.rst', 'r', encoding='utf-8').read(),
      author='David Fischer',
      author_email='david.fischer.ch@gmail.com',
      url='https://github.com/davidfischer-ch/pytoolbox_bin',
      license='EUPL 1.1',
      classifiers=filter(None, classifiers.split('\n')),
      keywords=['download', 'gdata', 'github', 'songs', 'youtube'],
      install_requires=[str(requirement.req) for requirement in parse_requirements('REQUIREMENTS.txt')],
      tests_require=['coverage', 'mock', 'nose'],
      entry_points={
          'console_scripts': [
              'github-clone-starred=pytoolbox_bin.github.bin:clone_starred',
              'youtube-download-likes=pytoolbox_bin.youtube.bin:download_likes',
              'socket-fec-generator=pytoolbox_bin.smpte2022.bin:socket_fec_generator',
              'twisted-fec-generator=pytoolbox_bin.smpte2022.bin:twisted_fec_generator'
          ]
      },
      # Thanks to https://github.com/graingert/django-browserid/commit/46c763f11f76b2f3ba365b164196794a37494f44
      test_suite='tests.pytoolbox_bin_runtests.main', **kwargs)
