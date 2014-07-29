
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

import doctest, errno, logging, signal, socket
from pytoolbox.encoding import configure_unicode
from pytoolbox.logging import setup_logging
from pytoolbox.network.ip import IPSocket
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType

log = logging.getLogger('smpte2022lib')


def socket_fec_generator():
    """
    This is a working example utility using this class, this method will :

    * Parse arguments from command line
    * Register handlers to SIGTERM and SIGINT
    * Instantiate a :mod:`SocketFecGenerator` and start it
    """
    from .lib import SocketFecGenerator

    configure_unicode()
    setup_logging(name='smpte2022lib', filename=None, console=True, level=logging.DEBUG)
    log.info('Testing SocketFecGenerator with doctest')
    doctest.testmod(verbose=False)
    log.info('OK')

    HELP_MEDIA   = 'Socket of input stream'
    HELP_COL     = 'Socket of generated FEC column stream'
    HELP_ROW     = 'Socket of generated FEC row stream'
    HELP_L       = 'Horizontal size of the FEC matrix (columns)'
    HELP_D       = 'Vertical size of the FEC matrix (rows)'
    HELP_TIMEOUT = 'Set timeout for socket operations (in seconds)'
    HELP_PROFILE = 'Set profiling output file (this enable profiling)'
    HELP_STOP    = 'Automatic stop time (in seconds)'

    dmedia = SocketFecGenerator.DEFAULT_MEDIA
    dcol = SocketFecGenerator.DEFAULT_COL
    drow = SocketFecGenerator.DEFAULT_ROW

    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        epilog='''This utility create SMPTE 2022-1 FEC streams from a sniffed source stream.
                   SMPTE 2022-1 help streaming systems to improve QoE of real-time RTP transmissions.''')
    parser.add_argument('-m', '--media',        type=IPSocket,      help=HELP_MEDIA,   default=dmedia)
    parser.add_argument('-c', '--col',          type=IPSocket,      help=HELP_COL,     default=dcol)
    parser.add_argument('-r', '--row',          type=IPSocket,      help=HELP_ROW,     default=drow)
    parser.add_argument('-l',                   type=int,           help=HELP_L,       default=5)
    parser.add_argument('-d',                   type=int,           help=HELP_D,       default=6)
    parser.add_argument('-t', '--timeout',      type=int,           help=HELP_TIMEOUT, nargs='?', default=None)
    parser.add_argument('-s', '--stop-time',    type=int,           help=HELP_STOP,    nargs='?', default=None)
    parser.add_argument('-p', '--profile',      type=FileType('w'), help=HELP_PROFILE, nargs='?', default=None)
    args = parser.parse_args()

    def handle_stop_signal(SIGNAL, stack):
        generator.stop()

    try:
        signal.signal(signal.SIGTERM, handle_stop_signal)
        signal.signal(signal.SIGINT, handle_stop_signal)
        generator = SocketFecGenerator(args.media, args.col, args.row, args.l, args.d)
        if args.profile:
            from pycallgraph import PyCallGraph
            from pycallgraph.output import GraphvizOutput
            with PyCallGraph(output=GraphvizOutput(output_file=args.profile.name)):
                generator.run(args.timeout, args.stop_time)
        else:
            generator.run(args.timeout, args.stop_time)
    except socket.error as e:
        if e.errno != errno.EINTR:
            raise


def twisted_fec_generator():
    """
    This is a working example utility using this class, this method will :

    * Parse arguments from command line
    * Register handlers to SIGTERM and SIGINT
    * Instantiate a :mod:`TwistedFecGenerator` and start it
    """
    from twisted.internet import reactor
    from .lib import TwistedFecGenerator

    configure_unicode()
    setup_logging(name='smpte2022lib', filename=None, console=True, level=logging.DEBUG)
    log.info('Testing TwistedFecGenerator with doctest')
    doctest.testmod(verbose=False)
    log.info('OK')

    HELP_MEDIA   = 'Socket of input stream'
    HELP_COL     = 'Socket of generated FEC column stream'
    HELP_ROW     = 'Socket of generated FEC row stream'
    HELP_L       = 'Horizontal size of the FEC matrix (columns)'
    HELP_D       = 'Vertical size of the FEC matrix (rows)'
    HELP_PROFILE = 'Set profiling output file (this enable profiling)'

    dmedia = TwistedFecGenerator.DEFAULT_MEDIA
    dcol = TwistedFecGenerator.DEFAULT_COL
    drow = TwistedFecGenerator.DEFAULT_ROW

    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        epilog='''This utility create SMPTE 2022-1 FEC streams from a sniffed source stream.
                   SMPTE 2022-1 help streaming systems to improve QoE of real-time RTP transmissions.''')
    parser.add_argument('-m', '--media',   type=IPSocket,      help=HELP_MEDIA,   default=dmedia)
    parser.add_argument('-c', '--col',     type=IPSocket,      help=HELP_COL,     default=dcol)
    parser.add_argument('-r', '--row',     type=IPSocket,      help=HELP_ROW,     default=drow)
    parser.add_argument('-l',              type=int,           help=HELP_L,       default=5)
    parser.add_argument('-d',              type=int,           help=HELP_D,       default=6)
    parser.add_argument('-p', '--profile', type=FileType('w'), help=HELP_PROFILE, nargs='?', default=None)
    args = parser.parse_args()

    def handle_stop_signal(SIGNAL, stack):
        log.info('\nGenerator stopped\n')
        reactor.stop()

    try:
        signal.signal(signal.SIGTERM, handle_stop_signal)
        signal.signal(signal.SIGINT, handle_stop_signal)

        # FIXME port ?
        TwistedFecGenerator(args.media['ip'], 'MyGenerator', args.col, args.row, args.l, args.d)
        # Disabled otherwise multicast packets are received twice !
        # See ``sudo watch ip maddr show`` they will be 2 clients if uncommented :
        # reactor.run() vs -> reactor.listenMulticast(args.media['port'], generator, listenMultiple=True) <-

        if args.profile:
            from pycallgraph import PyCallGraph
            from pycallgraph.output import GraphvizOutput
            with PyCallGraph(output=GraphvizOutput(output_file=args.profile.name)):
                reactor.run()
        else:
            reactor.run()
    except socket.error as e:
        if e.errno != errno.EINTR:
            raise
