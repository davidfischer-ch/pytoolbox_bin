# -*- encoding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import logging, socket, struct, time
from pytoolbox.encoding import to_bytes
from pytoolbox.network.rtp import RtpPacket
from pytoolbox.network.smpte2022.generator import FecGenerator

log = logging.getLogger('smpte2022lib')


# FIXME send to multicast address fail (?)
class SocketFecGenerator(object):
    """
    A SMPTE 2022-1 FEC streams generator with network skills based on :mod:`socket`.

    This generator listen to incoming RTP media stream, compute and output corresponding FEC streams.

    **Example usage**

    >>> from pytoolbox.network.ip import IPSocket
    >>> media = IPSocket(SocketFecGenerator.DEFAULT_MEDIA)
    >>> col = IPSocket(SocketFecGenerator.DEFAULT_COL)
    >>> row = IPSocket(SocketFecGenerator.DEFAULT_ROW)
    >>> generator = SocketFecGenerator(media, col, row, 5, 6)
    >>> print(generator._generator)
    Matrix size L x D            = 5 x 6
    Total invalid media packets  = 0
    Total media packets received = 0
    Column sequence number       = 1
    Row    sequence number       = 1
    Media  sequence number       = None
    Medias buffer (seq. numbers) = []
    """

    DEFAULT_MEDIA = '239.232.0.222:5004'
    DEFAULT_COL = '239.232.0.222:5006'
    DEFAULT_ROW = '239.232.0.222:5008'

    def __init__(self, media_socket, col_socket, row_socket, L, D):
        """
        Construct a SocketFecGenerator.

        :param media_socket: Socket of incoming RTP media stream
        :type media_socket: IPSocket
        :param col_socket: Socket of output FEC stream (column)
        :type col_socket: IPSocket
        :param row_socket: Socket of output FEC stream (row)
        :type row_socket: IPSocket
        :param L: Horizontal size of the FEC matrix (columns)
        :type L: int
        :param D: Vertical size of the FEC matrix (rows)
        :type D: int
        """
        self.media_socket = media_socket
        self.col_socket = col_socket
        self.row_socket = row_socket
        self._generator = FecGenerator(L, D)
        self._generator.on_new_col = self.on_new_col
        self._generator.on_new_row = self.on_new_row
        self._generator.on_reset = self.on_reset
        self._running = False

    @property
    def running(self):
        """Return True if FEC generator is running."""
        return self._running

    def run(self, timeout, stop_time=None):
        """
        Run FEC generator main loop.

        .. note::

            * Raise an exception if called when FEC generator is already running.
            * If ``timeout`` is None then this method will uses blocking socket operations:
                -> Stop requests may be never taken into account !

        :param timeout: Set a timeout on blocking socket operations (in seconds, or None).
        :type timeout: float

        **Example usage**

        >> print('TODO lazy developer !')
        I've done the code, but not the example ... I will do it later ...
        """
        if self._running:
            raise NotImplementedError(to_bytes('SMPTE 2022-1 FEC Generator already running'))
        try:
            self._running = True
            log.info('SMPTE 2022-1 FEC Generator by David Fischer')
            log.info('Started listening {0}'.format(self.media_socket))
            if stop_time:
                timeout = timeout or 1.0  # Ensure a time-out to handle stop time
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            sock.bind((self.media_socket['ip'], self.media_socket['port']))
            # Tell the operating system to add the socket to the multicast group on all interfaces
            group = socket.inet_aton(self.media_socket['ip'])
            mreq = struct.pack(b'4sL', group, socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            sock.settimeout(timeout)  # Time-out must be enabled to react to stop requests
            while self._running:      # Receive loop
                try:
                    datagram, address = sock.recvfrom(1024)
                    media = RtpPacket(bytearray(datagram), len(datagram))
                    log.debug('Incoming media packet seq={0} ts={1} psize={2} ssrc={3} address={4}'.format(
                              media.sequence, media.timestamp, media.payload_size, media.ssrc, address))
                    self._generator.put_media(media)
                except socket.timeout:
                    pass  # Handle time-out by doing nothing more than re-looping
                delta_time = time.time() - start_time
                if stop_time and delta_time > stop_time:
                    break
            log.info('Stopped listening {0} after {1} seconds'.format(self.media_socket, delta_time))
        finally:
            self.stop()

    def stop(self):
        """
        Ask the FEC generator to stop.

        The request will be taken into account by generator's main loop.
        Polling interval correspond to ``run()`` ``timeout`` parameter.
        """
        log.info('\nGenerator stopped\n')
        self._running = False

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
