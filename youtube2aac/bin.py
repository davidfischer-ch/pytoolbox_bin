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

import argparse, httplib2, json, sys
from os.path import abspath, expanduser, join
from codecs import open
from apiclient import discovery
from oauth2client import file
from oauth2client import client
from oauth2client import tools
from pytoolbox.filesystem import try_makedirs
#import pafy
#from youtube_dl.YoutubeDL import YoutubeDL


description = u'Download and convert to AAC your favorite songs.'


def main():

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter, epilog=description, parents=[tools.argparser])
    #parser.add_arguments(u'-o', u'--output', action=u'store', help=u'TODO', default=expanduser(u'~/.youtube2aac'))
    flags = parser.parse_args(sys.argv[1:])

    config_path = lambda *x: join(abspath(expanduser(u'~/.youtube2aac')), *x)
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
        credentials = tools.run_flow(flow, storage, flags)

    # Construct the service object to interact with the YouTube Data API.
    http = credentials.authorize(httplib2.Http())
    service = discovery.build(u'youtube', u'v3', http=http)

    try:
        page = None
        likes = []
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
        for like in likes:
            print(like)
            #YoutubeDL() or pafy
        print(u'Success!')

    except client.AccessTokenRefreshError:
        print(u'The credentials have been revoked or expired, please re-run the app to re-authorize')


if __name__ == u'__main__':
    main()
