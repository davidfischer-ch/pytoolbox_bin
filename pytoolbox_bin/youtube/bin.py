# -*- coding: utf-8 -*-

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

import argparse, httplib2, os, json, sys
from codecs import open
from apiclient import discovery
from oauth2client import client, file, tools
from os.path import abspath, expanduser, join, splitext
from pytoolbox.encoding import configure_unicode
from pytoolbox.filesystem import try_makedirs, try_remove
from pytoolbox.network.http import download
from youtube_dl.YoutubeDL import YoutubeDL

from .lib import remove_special_chars
from ..common import config_path


def download_likes():
    u"""Download and convert to AAC your favorite songs."""

    configure_unicode()
    HELP_OUTPUT, DEFAULT_OUTPUT = 'Download directory', abspath(expanduser('~/youtube_likes'))
    HELP_UPDATE, DEFAULT_UPDATE = 'Request the likes with the YouTube API', True
    HELP_THUMBNAIL, DEFAULT_THUMBNAIL = 'Download the thumbnails', False
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     epilog=download_likes.__doc__, parents=[tools.argparser])
    parser.add_argument('-o', '--output',    action='store',      help=HELP_OUTPUT,    default=DEFAULT_OUTPUT)
    parser.add_argument('-t', '--thumbnail', action='store_true', help=HELP_THUMBNAIL, default=DEFAULT_THUMBNAIL)
    parser.add_argument('-u', '--update',    action='store_true', help=HELP_UPDATE,    default=DEFAULT_UPDATE)
    args = parser.parse_args(sys.argv[1:])

    output_path = lambda *x: join(abspath(expanduser(args.output)), *x)
    try_makedirs(config_path(''))

    # Name of a file containing the OAuth 2.0 token, <https://cloud.google.com/console#/project/947551927891/apiui>
    client_secrets_filename = config_path('client_secrets.json')

    # Set up a Flow object to be used for authentication. PLEASE ONLY ADD THE SCOPES YOU NEED.
    # See <https://developers.google.com/+/best-practices>
    flow = client.flow_from_clientsecrets(client_secrets_filename, scope=[
        'https://www.googleapis.com/auth/youtube',
        'https://www.googleapis.com/auth/youtube.readonly',
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtubepartner',
        'https://www.googleapis.com/auth/youtubepartner-channel-audit',
    ], message=tools.message_if_missing(client_secrets_filename))

    # If the credentials don't exist or are invalid run through the native client flow.
    # The Storage object will ensure that if successful the good credentials will get written back to the file.
    storage = file.Storage(config_path('credentials.dat'))
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage, args)

    # Construct the service object to interact with the YouTube Data API.
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('youtube', 'v3', http=http)
    likes_filename = config_path('likes.json')

    likes = []
    if not args.update:
        try:
            with open(likes_filename, 'r', 'utf-8') as f:
                likes = json.loads(f.read())
        except IOError:
            pass

    videos_names = set()
    for root, dirnames, filenames in os.walk(output_path()):
        for filename in filenames:
            videos_names.add(unicode(splitext(filename)[0], 'utf-8'))

    if not likes:
        try:
            page = None
            while True:
                print('Read page {0}'.format(page))
                response = service.videos().list(part='id,snippet', myRating='like', maxResults=50,
                                                 pageToken=page).execute()
                likes += response['items']
                page = response.get('nextPageToken')
                if not page:
                    break
            print('Retrieved {0} likes from your activity in YouTube.'.format(len(likes)))
            with open(likes_filename, 'w', 'utf-8') as f:
                f.write(json.dumps(likes))
        except client.AccessTokenRefreshError:
            print('The credentials have been revoked or expired, please re-run the application to re-authorize')

    deleted_ids = set()
    for like in likes:
        video_id = like['id']
        video_title = like['snippet']['title']
        video_name = remove_special_chars(video_title) + '_' + video_id

        if video_name in videos_names:
            print('Skip already downloaded video {0}'.format(video_title))
        elif 'Deleted video' in video_name:
            deleted_ids.add(video_id)
        else:
            print('Downloading video {0}'.format(video_title))
            video_path, thumbnail_path = output_path(video_name + '.mp4'), output_path(video_name + '.jpg')
            ydl = YoutubeDL({'outtmpl': video_path})
            ydl.add_default_info_extractors()
            try:
                ydl.download([video_id])
                if args.thumbnail:
                    download(like['snippet']['thumbnails']['high']['url'], thumbnail_path)
            except Exception as e:
                print('Download failed, reason: {0}'.format(repr(e)), file=sys.stderr)
                try_remove(video_path)
                if args.thumbnail:
                    try_remove(thumbnail_path)

    print('Successfully downloaded {0} likes!'.format(len(likes)))
    print('There are {0} deleted likes: {1}'.format(len(deleted_ids), deleted_ids))
