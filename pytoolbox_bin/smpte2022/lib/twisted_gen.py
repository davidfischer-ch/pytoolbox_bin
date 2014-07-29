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

import logging, socket
from pytoolbox.network.rtp import RtpPacket
from pytoolbox.network.smpte2022.generator import FecGenerator
from twisted.internet.protocol import DatagramProtocol

log = logging.getLogger('smpte2022lib')


# FIXME send to multicast address fail (?)
class TwistedFecGenerator(DatagramProtocol):
    """
    A SMPTE 2022-1 FEC streams generator with network skills based on :mod:`twisted`.

    This generator listen to incoming RTP media stream, compute and output corresponding FEC streams.
    It is required to use reactor in order to run the generator.

    **Example usage**

    >>> from pytoolbox.network.ip import IPSocket
    >>> from twisted.internet import reactor
    >>> media = IPSocket(TwistedFecGenerator.DEFAULT_MEDIA)
    >>> col = IPSocket(TwistedFecGenerator.DEFAULT_COL)
    >>> row = IPSocket(TwistedFecGenerator.DEFAULT_ROW)
    >>> generator = TwistedFecGenerator(media['ip'], 'MyTwistedFecGenerator', col, row, 5, 6)
    >>> reactor.listenMulticast(media['port'], generator, listenMultiple=True) # doctest: +ELLIPSIS
    <....TwistedFecGenerator... on 5004>
    >>> print(generator._generator)
    Matrix size L x D            = 5 x 6
    Total invalid media packets  = 0
    Total media packets received = 0
    Column sequence number       = 1
    Row    sequence number       = 1
    Media  sequence number       = None
    Medias buffer (seq. numbers) = []

    Then you only need to start reactor with ``reactor.run()``.
    """

    DEFAULT_MEDIA = '239.232.0.222:5004'
    DEFAULT_COL = '127.0.0.1:5006'  # '239.232.0.222:5006'
    DEFAULT_ROW = '127.0.0.1:5008'  # '239.232.0.222:5008'

    def __init__(self, group, name, col_socket, row_socket, L, D):
        """
        Construct a TwistedFecGenerator.

        :param group: IP address of incoming RTP media stream
        :type group: str
        :param name: Name of current instance (reactor's stuff)
        :type name: str
        :param col_socket: Socket of output FEC stream (column)
        :type col_socket: IPSocket
        :param row_socket: Socket of output FEC stream (row)
        :type row_socket: IPSocket
        :param L: Horizontal size of the FEC matrix (columns)
        :type L: int
        :param D: Vertical size of the FEC matrix (rows)
        :type D: int
        """
        self.group = group
        self.name = name
        self.col_socket = col_socket
        self.row_socket = row_socket
        self._generator = FecGenerator(L, D)
        self._generator.on_new_col = self.on_new_col
        self._generator.on_new_row = self.on_new_row
        self._generator.on_reset = self.on_reset

    def startProtocol(self):
        log.info('SMPTE 2022-1 FEC Generator by David Fischer')
        log.info('started Listening {0}'.format(self.group))
        self.transport.joinGroup(self.group)
        self.transport.setLoopbackMode(False)
        self.transport.setTTL(1)

    def datagramReceived(self, datagram, socket):
        media = RtpPacket(bytearray(datagram), len(datagram))
        log.debug('Incoming media packet seq={0} ts={1} psize={2} socket={3}'.format(
                  media.sequence, media.timestamp, media.payload_size, socket))
        self._generator.put_media(media)

    def on_new_col(self, col, generator):
        """
        Called by ``self=FecGenerator`` when a new column FEC packet is generated and available for output.

        Send the encapsulated column FEC packet.

        :param col: Generated column FEC packet
        :type col: FecPacket
        :param generator: The generator that fired this method / event
        :type generator: FecGenerator
        """
        col_rtp = RtpPacket.create(col.sequence, 0, RtpPacket.DYNAMIC_PT, col.bytes)
        log.debug('Send COL FEC packet seq={0} snbase={1} LxD={2}x{3} trec={4} socket={5}'.format(
                  col.sequence, col.snbase, col.L, col.D, col.timestamp_recovery, self.col_socket))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.sendto(col_rtp.bytes, (self.col_socket['ip'], self.col_socket['port']))

    def on_new_row(self, row, generator):
        """
        Called by ``self=FecGenerator`` when a new row FEC packet is generated and available for output.

        Send the encapsulated row FEC packet.

        :param row: Generated row FEC packet
        :type row: FecPacket
        :param generator: The generator that fired this method / event
        :type generator: FecGenerator
        """
        row_rtp = RtpPacket.create(row.sequence, 0, RtpPacket.DYNAMIC_PT, row.bytes)
        log.debug('Send ROW FEC packet seq={0} snbase={1} LxD={2}x{3} trec={4} socket={5}'.format(
                  row.sequence, row.snbase, row.L, row.D, row.timestamp_recovery, self.row_socket))
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.sendto(row_rtp.bytes, (self.row_socket['ip'], self.row_socket['port']))

    def on_reset(self, media, generator):
        """
        Called by ``self=FecGenerator`` when the algorithm is resetted (an incoming media is out of sequence).

        Log a warning message.

        :param media: Out of sequence media packet
        :type row: RtpPacket
        :param generator: The generator that fired this method / event
        :type generator: FecGenerator
        """
        log.warning('Media seq={0} is out of sequence (expected {1}) : FEC algorithm resetted !'.format(
                    media.sequence, generator._media_sequence))
