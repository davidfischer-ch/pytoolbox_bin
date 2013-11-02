#!/usr/bin/env python
# -*- coding: utf-8 -*-

#**********************************************************************************************************************#
#                             YOUTUBE 2 AAC - DOWNLOAD AND CONVERT TO AAC YOUR FAVORITE SONGS
#
#  Main Developer : David Fischer (david.fischer.ch@gmail.com)
#  Copyright      : Copyright (c) 2013 David Fischer. All rights reserved.
#
#**********************************************************************************************************************#
#
# This file is part of David Fischer's youtube2aac Project.
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
# Retrieved from https://github.com/davidfischer-ch/youtube2aac.git

from __future__ import absolute_import, division, print_function, unicode_literals

import argparse, httplib2, json, sys, urllib2
from os.path import abspath, exists, expanduser, join
from codecs import open
from apiclient import discovery
from oauth2client import file
from oauth2client import client
from oauth2client import tools
from pytoolbox.filesystem import try_makedirs
from youtube_dl.YoutubeDL import YoutubeDL


description = u'Download and convert to AAC your favorite songs.'
HELP_OUTPUT = u'Download directory'

def main():

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, epilog=description, parents=[tools.argparser])
    parser.add_argument(u'-o', u'--output', action=u'store', help=HELP_OUTPUT, default=expanduser(u'~/youtube2aac'))
    args = parser.parse_args(sys.argv[1:])
    update = True  # FIXME add as argument to parser

    config_path = lambda *x: join(abspath(expanduser(u'~/.youtube2aac')), *x)
    output_path = lambda *x: join(abspath(expanduser(args.output)), *x)
    try_makedirs(config_path(u''))

    # Name of a file containing the OAuth 2.0 token, <https://cloud.google.com/console#/project/947551927891/apiui>
    client_secrets = config_path(u'client_secrets.json')

    # Set up a Flow object to be used for authentication. PLEASE ONLY ADD THE SCOPES YOU NEED.
    # See <https://developers.google.com/+/best-practices>
    flow = client.flow_from_clientsecrets(client_secrets, scope=[
        u'https://www.googleapis.com/auth/youtube',
        u'https://www.googleapis.com/auth/youtube.readonly',
        u'https://www.googleapis.com/auth/youtube.upload',
        u'https://www.googleapis.com/auth/youtubepartner',
        u'https://www.googleapis.com/auth/youtubepartner-channel-audit',
    ], message=tools.message_if_missing(client_secrets))

    # If the credentials don't exist or are invalid run through the native client flow.
    # The Storage object will ensure that if successful the good credentials will get written back to the file.
    storage = file.Storage(config_path(u'credentials.dat'))
    credentials = storage.get()
    if credentials is None or credentials.invalid:
        credentials = tools.run_flow(flow, storage, args)

    # Construct the service object to interact with the YouTube Data API.
    http = credentials.authorize(httplib2.Http())
    service = discovery.build(u'youtube', u'v3', http=http)

    try:
        with open(config_path(u'likes.json'), u'r', u'utf-8') as f:
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
            print(u'Retrieved {0} likes from your activity in YouTube.'.format(len(likes)))
            with open(config_path(u'likes.json'), u'w', u'utf-8') as f:
                f.write(json.dumps(likes))
        except client.AccessTokenRefreshError:
            print(u'The credentials have been revoked or expired, please re-run the app to re-authorize')

    for like in likes:
        video_title, video_id = like[u'snippet'][u'title'], like[u'contentDetails'][u'like'][u'resourceId'][u'videoId']
        thumbnail_path = output_path(u'{0}_thumbnails.jpg'.format(video_title))
        if exists(thumbnail_path):
            print(u'Skip already downloaded video {0}'.format(video_title))
        else:
            print(u'Download video {0}'.format(video_title))
            download(like[u'snippet'][u'thumbnails'][u'high'][u'url'], thumbnail_path)
            ydl = YoutubeDL({u'outtmpl': output_path(u'%(title)s_%(id)s')})  # u'simulate': True,
            ydl.add_default_info_extractors()
            ydl.download([video_id])

    print(u'Success!')

def download(url, filename):
    with open(filename, u'wb') as f:
        f.write(urllib2.urlopen(url).read())

# ----------------------------------------------------------------------------------------------------------------------

if __name__ == u'__main__':
    main()
