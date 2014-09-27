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

import argparse, httplib2, json, os, sys
from codecs import open
from apiclient import discovery
from oauth2client import client, file, tools
from os.path import abspath, expanduser, join
from pytoolbox.encoding import configure_unicode
from pytoolbox.filesystem import try_makedirs, try_remove
from pytoolbox.network.http import download
from pytoolbox.serialization import object_to_json
from youtube_dl.YoutubeDL import YoutubeDL

from .lib import Like
from ..common import error, config_path


def download_likes():
    u"""Download and convert to AAC your favorite songs."""

    configure_unicode()
    HELP_OUTPUT, DEFAULT_OUTPUT = 'Download directory', abspath(expanduser('~/youtube_likes'))
    HELP_UPDATE = 'Request the likes with the YouTube API'
    HELP_THUMBNAIL, DEFAULT_THUMBNAIL = 'Download the thumbnails', False
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     epilog=download_likes.__doc__, parents=[tools.argparser])
    parser.add_argument('-o', '--output',    action='store',       help=HELP_OUTPUT,    default=DEFAULT_OUTPUT)
    parser.add_argument('-t', '--thumbnail', action='store_true',  help=HELP_THUMBNAIL, default=DEFAULT_THUMBNAIL)
    parser.add_argument('-u', '--update',    action='store_false', help=HELP_UPDATE)
    args = parser.parse_args(sys.argv[1:])

    output_directory = abspath(expanduser(args.output))
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
                likes = [Like(**like_dict) for like_dict in json.loads(f.read())]
        except IOError:
            pass

    local_likes = {}
    for dirpath, dirnames, filenames in os.walk(output_directory):
        for filename in (unicode(f, 'utf-8') for f in filenames):
            like = Like.from_filename(join(dirpath, filename))
            if not like:
                error('Unable to parse components of filename "{0}"'.format(filename), 1)
            local_likes.setdefault(like.id, like)

    if not likes:
        try:
            page = None
            while True:
                print('Read page {0}'.format(page))
                response = service.videos().list(part='id,snippet', myRating='like', maxResults=50,
                                                 pageToken=page).execute()
                likes += [Like.from_api_response(item, output_directory) for item in response['items']]
                page = response.get('nextPageToken')
                if not page:
                    break
            print('Retrieved {0} likes from your activity in YouTube.'.format(len(likes)))
            with open(likes_filename, 'w', 'utf-8') as f:
                f.write(object_to_json(likes, include_properties=False))
        except client.AccessTokenRefreshError:
            error('The credentials have been revoked or expired, please re-run the application to re-authorize', 2)

    deleted_ids = set()
    errored_ids = set()
    downloaded = renamed = 0
    for like in likes:
        if like.deleted:
            deleted_ids.add(like.id)
        else:
            local_like = local_likes.get(like.id)
            if local_like:
                like.directory = local_like.directory
                if like.video != local_like.video:
                    print('Rename already downloaded video "{0.title}" to "{1.title}"'.format(local_like, like))
                    renamed += 1
                    os.rename(local_like.video, like.video)
                else:
                    print('Skip already downloaded video "{0.title}"'.format(local_like))
            else:
                print('Downloading video "{0.title}"'.format(like))
                ydl = YoutubeDL({'outtmpl': like.video})
                ydl.add_default_info_extractors()
                try:
                    ydl.download([like.id])
                    if args.thumbnail:
                        download(like.thumbnail_url, like.thumbnail)
                    downloaded += 1
                except Exception as e:
                    error('Download failed, reason: {0}'.format(repr(e)), None)
                    errored_ids.add(like.id)
                    try_remove(like.video)
                    if args.thumbnail:
                        try_remove(like.thumbnail)

    print('Successfully processed {0} likes! (renamed {1} and downloaded {2})'.format(len(likes), renamed, downloaded))
    print('There are {0} deleted likes: {1}'.format(len(deleted_ids), deleted_ids))
    print('There are {0} error-ed likes: {1}'.format(len(errored_ids), errored_ids))
