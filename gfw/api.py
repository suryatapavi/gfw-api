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

"""This module contains API request handlers for Global Forest Watch."""

from gfw import forma
from gfw import imazon
from gfw import modis

import json
import os
import webapp2

# True if executing on dev server:
IS_DEV = os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')

# Matches a date in yyyy-mm-dd format from between 1900-01-01 and 2099-12-31.:
DATE_REGEX = r'(19|20)\d\d[- /.](0[1-9]|1[012])[- /.](0[1-9]|[12][0-9]|3[01])'

# Path to get aggregated FORMA alerts for supplied ISO.
# /{iso}/{startdate}/{enddate} where dates are in the form yyyy-mm-dd.
FORMA_ISO = r'/api/v1/defor/analyze/forma/iso/<:\w{3,3}>/<:%s>/<:%s>' \
    % (DATE_REGEX, DATE_REGEX)

# Path for aggregated defor values by dataset for dynamic polygon as GeoJSON:
FORMA_GEOJSON = r'/api/v1/defor/analyze/forma/<:%s>/<:%s>' \
    % (DATE_REGEX, DATE_REGEX)

MODIS_ISO = r'/api/v1/defor/analyze/modis/iso/<:\w{3,3}>/<:%s>' % DATE_REGEX
MODIS_GEOJSON = r'/api/v1/defor/analyze/modis/<:%s>' % DATE_REGEX

# Imazon defor value in BRA poly or GeoJSON for supplied date range.
# Note: Only data for 2008-2012
IMAZON = r'/api/v1/defor/analyze/imazon'

# API routes:
routes = [
    webapp2.Route(FORMA_ISO, handler='gfw.api.AnalyzeApi:forma_iso'),
    webapp2.Route(FORMA_GEOJSON, handler='gfw.api.AnalyzeApi:forma_geojson'),
    webapp2.Route(IMAZON, handler='gfw.api.AnalyzeApi:imazon'),
    webapp2.Route(MODIS_ISO, handler='gfw.api.AnalyzeApi:modis_iso'),
    webapp2.Route(MODIS_GEOJSON, handler='gfw.api.AnalyzeApi:modis_geojson'),
]


class AnalyzeApi(webapp2.RequestHandler):
    """Handler for aggregated defor values for supplied dataset and polygon."""

    def _send_response(self, result):
        """Sends supplied result dictionnary as JSON response."""
        self.response.headers.add_header("Access-Control-Allow-Origin", "*")
        self.response.headers['Access-Control-Allow-Headers'] = \
            'Origin, X-Requested-With, Content-Type, Accept'
        self.response.out.headers['Content-Type'] = 'application/json'
        self.response.headers['charset'] = 'utf-8'
        self.response.out.write(json.dumps(result))

    def options(self):
        """Options to support CORS requests."""
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.headers['Access-Control-Allow-Headers'] = \
            'Origin, X-Requested-With, Content-Type, Accept'
        self.response.headers['Access-Control-Allow-Methods'] = 'POST, GET'

    def imazon(self):
        """Return Imazon values for BRA or supplied GeoJSON poly."""
        try:
            geojson = json.loads(self.request.get('q'))
        except:
            geojson = None
        total_area = imazon.get_defor(geojson=geojson)
        result = {'units': 'meters', 'value': total_area,
                  'value_display': format(total_area, ",f")}
        self._send_response(result)

    def modis_iso(self, iso, date):
        """Return MODIS count for supplied ISO and date."""
        count = modis.get_count_by_iso(iso, date)
        result = {'units': 'count', 'value': count,
                  'value_display': format(count, ",d")}
        self._send_response(result)

    def modis_geojson(self, date):
        """Return MODIS count for supplied date and geojson polygon."""
        geojson = json.loads(self.request.get('q'))
        count = modis.get_count_by_geojson(geojson, date)
        result = {'units': 'alerts', 'value': count,
                  'value_display': format(count, ",d")}
        self._send_response(result)

    def forma_iso(self, iso, start_date, end_date):
        """Return FORMA alert count for supplied ISO and dates."""
        count = forma.get_alerts_by_iso(iso, start_date, end_date)
        result = {'units': 'alerts', 'value': count,
                  'value_display': format(count, ",d")}
        self._send_response(result)

    def forma_geojson(self, start_date, end_date):
        """Return FORMA alert count for supplied dates and geojson polygon."""
        geojson = json.loads(self.request.get('q'))
        count = forma.get_alerts_by_geojson(geojson, start_date, end_date)
        result = {'units': 'alerts', 'value': count,
                  'value_display': format(count, ",d")}
        self._send_response(result)


class DownloadApi(webapp2.RequestHandler):
    pass


class SubscribeApi(webapp2.RequestHandler):
    pass

handlers = webapp2.WSGIApplication(routes, debug=IS_DEV)
