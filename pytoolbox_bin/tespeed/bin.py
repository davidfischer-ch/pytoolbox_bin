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

import json, logging
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType
from codecs import open
from pytoolbox.encoding import configure_unicode
from pytoolbox.logging import setup_logging

from .lib import graph, measure


def isp_benchmark():
    """Benchmark your Internet connection and graph the speed over the time, based on tespeed and pygal."""

    configure_unicode()
    setup_logging(name='isp_benchmark', filename=None, console=True, level=logging.DEBUG)

    HELP_F = 'The path to a file with the results of a benchmark'
    HELP_G = 'Graph the results into a png and svg file'
    HELP_I = 'Interval for the measures, in minutes'
    HELP_M = 'Run the benchmark and save results into a json file'
    HELP_R = 'Time range to measure, in minutes'

    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter, epilog=isp_benchmark.__doc__)
    subparsers = parser.add_subparsers(dest='action', help=isp_benchmark.__doc__)

    measure_parser = subparsers.add_parser('measure', help=HELP_M)
    measure_parser.add_argument('-i', '--interval', type=int, help=HELP_I, default=15)
    measure_parser.add_argument('-r', '--range',    type=int, help=HELP_R, default=24*60)
    measure_parser.add_argument('-g', '--graph',    action='store_true', help=HELP_G)

    graph_parser = subparsers.add_parser('graph',  help=HELP_G)
    graph_parser.add_argument('results_file', type=FileType('r'), help=HELP_F)

    for p in (measure_parser, graph_parser):
        p.add_argument('-w', '--width',  type=int, default=1920)
        p.add_argument('-e', '--height', type=int, default=1080)

    args = parser.parse_args()

    if args.action == 'measure':
        results = measure(args.interval * 60, args.range * 60)
        if results:
            filename = 'isp-benchmark %s.json' % results[0]['date']
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(json.dumps(results))
            if args.graph:
                graph(open(filename, 'r'), width=args.width, height=args.height)

    elif args.action == 'graph':
        graph(args.results_file, width=args.width, height=args.height)
