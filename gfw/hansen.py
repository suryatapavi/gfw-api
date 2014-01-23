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

"""This module supports accessing hansen data."""

import json
import ee
import logging
import config

from gfw import cdb

ALL = """SELECT iso, year, sum(loss) loss, sum(loss_perc) loss_perc
         FROM hansen 
         WHERE iso ilike '{iso}' 
         GROUP BY iso, year 
         ORDER BY iso, year ASC"""

SUM = """SELECT iso, avg(treecover_2000) treecover_2000,
                avg(treecover_2000_perc) treecover_2000_perc,
                avg(gain) gain, avg(gain_perc) gain_perc,
                sum(loss) loss,
                sum(loss_perc) loss_perc
         FROM hansen 
         WHERE iso ilike '{iso}'
         GROUP BY iso"""

def _get_coords(geojson):
    return geojson.get('coordinates')


def _ee(params, asset_id):
    ee.Initialize(config.EE_CREDENTIALS, config.EE_URL)
    loss_by_year = ee.Image(config.assets[asset_id])
    poly = _get_coords(json.loads(params.get('geom')))
    params.pop('geom')
    params.pop('layer')
    if params.get('maxPixels'):
        params['maxPixels'] = int(params['maxPixels'])
    if params.get('tileScale'):
        params['tileScale'] = int(params['tileScale'])
    if params.get('scale'):
        params['scale'] = int(params['scale'])
    else:
        params['scale'] = 90
    if params.get('bestEffort'):
        params['bestEffort'] = bool(params['bestEffort'])
    else:
        params['bestEffort'] = True
    region = ee.Geometry.Polygon(poly)
    reduce_args = {
        'reducer': ee.Reducer.sum(),
        'geometry': region
    }
    reduce_args.update(params)
    area_stats = loss_by_year.divide(1000 * 1000 * 255.0) \
        .multiply(ee.Image.pixelArea()) \
        .reduceRegion(**reduce_args)
    area_results = area_stats.getInfo()
    area = ee.Image.pixelArea().reduceRegion(**reduce_args).get('area')
    percent_stats = loss_by_year.multiply(100.0 / 255.0) \
        .divide(ee.Image.constant(area)) \
        .multiply(ee.Image.pixelArea()) \
        .reduceRegion(**reduce_args)
    percent_results = percent_stats.getInfo()
    if asset_id == 'hansen_all':
        loss = area_results['loss']
        area_results.pop('loss')
        area_results['loss_sum'] = loss
        loss = percent_results['loss']
        percent_results.pop('loss')
        percent_results['loss_sum'] = loss        
    return dict(area=area_results, percent=percent_results)

def _percent(row):
    return row['year'], row['loss_perc']

def _area(row):
    return row['year'], row['loss']

def _cdb(iso, layer):
    if layer == 'sum':
        query = SUM.format(iso=iso)
        result = cdb.execute(query, {})
        if result:
            result = json.loads(result)['rows'][0]
            percent = dict(
                loss_sum=result['loss_perc'],
                treecover_2000=result['treecover_2000_perc'],
                gain=result['gain_perc'])
            area = dict(
                loss_sum=result['loss'],
                treecover_2000=result['treecover_2000'],
                gain=result['gain'])
            return dict(iso=iso, area=area, percent=percent)
    elif layer == 'all':
        query = ALL.format(iso=iso)
        result = cdb.execute(query, {})
        if result:
            rows = json.loads(result)['rows']
            percent = dict(map(_percent, rows))
            area = dict(map(_area, rows))
            return dict(iso=iso, area=area, percent=percent)


def download(params):
    pass


def analyze(params):
    layer = params.get('layer')
    geom = params.get('geom', None)
    if geom:
        geom = json.loads(geom)
        if layer == 'sum':
            result = _ee(params, 'hansen_all')
        else:
            result = _ee(params, 'hansen_loss')
        result['geom'] = geom
    else:
        iso = params.get('iso', None)
        if iso:
            result = _cdb(iso, layer)
    return result