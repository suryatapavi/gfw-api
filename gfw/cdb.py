# Global Forest Watch API
# Copyright (C) 2013 World Resource Institute
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""This module supports executing CartoDB queries."""

import logging
import urllib
from appengine_config import runtime_config
from google.appengine.api import urlfetch

# CartoDB endpoint:
if runtime_config.get('cdb_endpoint'):
    ENDPOINT = runtime_config.get('cdb_endpoint')
else:
    ENDPOINT = 'http://wri-01.cartodb.com/api/v1/sql'


def _get_api_key():
    """Return CartoDB API key stored in cdb.txt file."""
    return runtime_config.get('cdb_api_key')


def get_format(media_type):
    """Return CartoDB format for supplied GFW custorm media type."""
    tokens = media_type.split('.')
    if len(tokens) == 2:
        return ''
    else:
        return tokens[2].split('+')[0]


def execute(query, params={}, api_key=False):
    """Exectues supplied query on CartoDB and returns response body as JSON."""
    rpc = urlfetch.create_rpc(deadline=60)
    params['q'] = query
    if api_key:
        params['api_key'] = _get_api_key()
    url = '%s?%s' % (ENDPOINT, urllib.urlencode(params))
    logging.info(url)
    urlfetch.make_fetch_call(rpc, url)
    try:
        result = rpc.get_result()
        if result.status_code == 200:
            return result.content
    except urlfetch.DownloadError, e:
        logging.error("CartoDB SQL API Error: %s %s" % (e, query))