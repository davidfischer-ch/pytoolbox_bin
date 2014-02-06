#!/usr/bin/env python
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

import argparse, httplib2, json, sys
from os.path import abspath, exists, expanduser, join
from codecs import open
from apiclient import discovery
from oauth2client import client, file, tools
from pytoolbox.encoding import configure_unicode
from pytoolbox.filesystem import try_makedirs
from youtube_dl.YoutubeDL import YoutubeDL

from .lib import download
from ..common import config_path


def download_likes():
    u"""Download and convert to AAC your favorite songs."""

    configure_unicode()
    HELP_OUTPUT = u'Download directory'
    DEFAULT_OUTPUT = abspath(expanduser(u'~/youtube_likes'))
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     epilog=download_likes.__doc__, parents=[tools.argparser])
    parser.add_argument(u'-o', u'--output', action=u'store', help=HELP_OUTPUT, default=DEFAULT_OUTPUT)
    args = parser.parse_args(sys.argv[1:])
    update = True  # FIXME add as argument to parser

    output_path = lambda *x: join(abspath(expanduser(args.output)), *x)
    try_makedirs(config_path(u''))

    # Name of a file containing the OAuth 2.0 token, <https://cloud.google.com/console#/project/947551927891/apiui>
    client_secrets_filename = config_path(u'client_secrets.json')

    # Set up a Flow object to be used for authentication. PLEASE ONLY ADD THE SCOPES YOU NEED.
    # See <https://developers.google.com/+/best-practices>
    flow = client.flow_from_clientsecrets(client_secrets_filename, scope=[
        u'https://www.googleapis.com/auth/youtube',
        u'https://www.googleapis.com/auth/youtube.readonly',
        u'https://www.googleapis.com/auth/youtube.upload',
        u'https://www.googleapis.com/auth/youtubepartner',
        u'https://www.googleapis.com/auth/youtubepartner-channel-audit',
    ], message=tools.message_if_missing(client_secrets_filename))

    # If the credentials don't exist or are invalid run through the native client flow.
    # The Storage object will ensure that if successful the good credentials will get written back to the file.
    storage = file.Storage(config_path(u'credentials.dat'))
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage, args)

    # Construct the service object to interact with the YouTube Data API.
    http = credentials.authorize(httplib2.Http())
    service = discovery.build(u'youtube', u'v3', http=http)
    likes_filename = config_path(u'likes.json')
    try:
        with open(likes_filename, u'r', u'utf-8') as f:
            likes = json.loads(f.read())
    except IOError:
        likes = []

    if not likes or update:
        try:
            page = None
            while True:
                print(u'read page {0}'.format(page))
                response = service.activities().list(part=u'snippet,contentDetails', mine=True,
                                                     maxResults=50, pageToken=page).execute()
                likes += [item for item in response[u'items'] if u'like' in item[u'contentDetails']]
                page = response.get(u'nextPageToken')
                if not page:
                    break
            print(u'Retrieved {0} likes from your activity in YouTube (some are probably duplicates).'.format(
                  len(likes)))
            with open(likes_filename, u'w', u'utf-8') as f:
                f.write(json.dumps(likes))
        except client.AccessTokenRefreshError:
            print(u'The credentials have been revoked or expired, please re-run the app to re-authorize')

    videos_ids = set()
    for like in likes:
        video_id = like[u'contentDetails'][u'like'][u'resourceId'][u'videoId']
        if video_id in videos_ids:
            continue  # skip the duplicates
        videos_ids.add(video_id)
        video_title = like[u'snippet'][u'title']
        video_title_safe = video_title.replace(u'/', u'-').replace(u'|', u'-').replace(u':', u'-')
        thumbnail_path = output_path(video_title_safe + u'_thumbnails.jpg')
        if exists(thumbnail_path):
            print(u'Skip already downloaded video {0}'.format(video_title))
        else:
            print(u'Downloading video {0}'.format(video_title))
            ydl = YoutubeDL({u'outtmpl': output_path(video_title_safe + u'_' + video_id + u'.mp4')})
            ydl.add_default_info_extractors()
            try:
                ydl.download([video_id])
                download(like[u'snippet'][u'thumbnails'][u'high'][u'url'], thumbnail_path)
            except Exception as e:
                print(u'Download failed, reason: {0}'.format(repr(e)), file=sys.stderr)

    print(u'Successfully downloaded {0} likes!'.format(len(videos_ids)))
