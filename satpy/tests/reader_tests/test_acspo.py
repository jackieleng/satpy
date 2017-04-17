#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Module for testing the satpy.readers.acspo module.
"""

import os
import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest
import mock
from datetime import datetime, timedelta
import numpy as np
from satpy.readers.netcdf_utils import NetCDF4FileHandler

DEFAULT_FILE_DTYPE = np.uint16
DEFAULT_FILE_SHAPE = (10, 300)
DEFAULT_FILE_DATA = np.arange(DEFAULT_FILE_SHAPE[0] * DEFAULT_FILE_SHAPE[1],
                              dtype=DEFAULT_FILE_DTYPE).reshape(DEFAULT_FILE_SHAPE)
DEFAULT_FILE_FACTORS = np.array([2.0, 1.0], dtype=np.float32)
DEFAULT_LAT_DATA = np.linspace(45, 65, DEFAULT_FILE_SHAPE[1]).astype(DEFAULT_FILE_DTYPE)
DEFAULT_LAT_DATA = np.repeat([DEFAULT_LAT_DATA], DEFAULT_FILE_SHAPE[0], axis=0)
DEFAULT_LON_DATA = np.linspace(5, 45, DEFAULT_FILE_SHAPE[1]).astype(DEFAULT_FILE_DTYPE)
DEFAULT_LON_DATA = np.repeat([DEFAULT_LON_DATA], DEFAULT_FILE_SHAPE[0], axis=0)


def get_test_content(filename, filename_info, filetype_info):
    dt = filename_info.get('start_time', datetime(2016, 1, 1, 12, 0, 0))
    sat, inst = {
        'VIIRS_NPP': ('NPP', 'VIIRS'),
    }[filename_info['sensor_id']]

    file_content = {
        '/attr/platform': sat,
        '/attr/sensor': inst,
        '/attr/spatial_resolution': '742 m at nadir',
        '/attr/time_coverage_start': dt.strftime('%Y%m%dT%H%M%SZ'),
        '/attr/time_coverage_end': (dt + timedelta(minutes=6)).strftime('%Y%m%dT%H%M%SZ'),
    }

    file_content['lat'] = DEFAULT_LAT_DATA
    file_content['lat/attr/comment'] = 'Latitude of retrievals'
    file_content['lat/attr/long_name'] = 'latitude'
    file_content['lat/attr/standard_name'] = 'latitude'
    file_content['lat/attr/units'] = 'degrees_north'
    file_content['lat/attr/valid_min'] = -90.
    file_content['lat/attr/valid_max'] = 90.
    file_content['lat/shape'] = DEFAULT_FILE_SHAPE

    file_content['lon'] = DEFAULT_LON_DATA
    file_content['lon/attr/comment'] = 'Longitude of retrievals'
    file_content['lon/attr/long_name'] = 'longitude'
    file_content['lon/attr/standard_name'] = 'longitude'
    file_content['lon/attr/units'] = 'degrees_east'
    file_content['lon/attr/valid_min'] = -180.
    file_content['lon/attr/valid_max'] = 180.
    file_content['lon/shape'] = DEFAULT_FILE_SHAPE

    for k in ['sea_surface_temperature',
              'satellite_zenith_angle',
              'sea_ice_fraction',
              'wind_speed']:
        file_content[k] = DEFAULT_FILE_DATA
        file_content[k + '/attr/scale_factor'] = 1.1
        file_content[k + '/attr/add_offset'] = 0.1
        file_content[k + '/attr/units'] = 'some_units'
        file_content[k + '/attr/comment'] = 'comment'
        file_content[k + '/attr/standard_name'] = 'standard_name'
        file_content[k + '/attr/long_name'] = 'long_name'
        file_content[k + '/attr/valid_min'] = 0
        file_content[k + '/attr/valid_max'] = 65534
        file_content[k + '/attr/_FillValue'] = 65534
        file_content[k + '/shape'] = DEFAULT_FILE_SHAPE

    file_content['l2p_flags'] = np.zeros(
        (1, DEFAULT_FILE_SHAPE[0], DEFAULT_FILE_SHAPE[1]),
        dtype=np.uint16)

    return file_content


class FakeNetCDF4FileHandler(NetCDF4FileHandler):
    def __init__(self, filename, filename_info, filetype_info, **kwargs):
        super(NetCDF4FileHandler, self).__init__(filename, filename_info, filetype_info)
        self.file_content = get_test_content(filename, filename_info, filetype_info)
        self.file_content.update(kwargs)


class TestACSPOReader(unittest.TestCase):
    yaml_file = "acspo.yaml"

    def setUp(self):
        from satpy.config import config_search_paths
        self.reader_configs = config_search_paths(os.path.join('readers', self.yaml_file))
        self.p = mock.patch('satpy.readers.netcdf_utils.NetCDF4FileHandler', FakeNetCDF4FileHandler)
        self.fake_base_handler = self.p.start()

    def tearDown(self):
        self.p.stop()

    def test_init(self):
        """Test basic init with no extra parameters."""
        from satpy.readers import load_reader
        r = load_reader(self.reader_configs)
        loadables = r.select_files_from_pathnames([
            '20170401174600-STAR-L2P_GHRSST-SSTskin-VIIRS_NPP-ACSPO_V2.40-v02.0-fv01.0.nc',
        ])
        self.assertTrue(len(loadables), 1)
        r.create_filehandlers(loadables)
        # make sure we have some files
        self.assertTrue(r.file_handlers)

    def test_load_every_m_band_bt(self):
        """Test loading all datasets"""
        from satpy.readers import load_reader
        r = load_reader(self.reader_configs)
        loadables = r.select_files_from_pathnames([
            '20170401174600-STAR-L2P_GHRSST-SSTskin-VIIRS_NPP-ACSPO_V2.40-v02.0-fv01.0.nc',
        ])
        r.create_filehandlers(loadables)
        datasets = r.load(['sst',
                           'satellite_zenith_angle',
                           'sea_ice_fraction',
                           'wind_speed'])
        self.assertEqual(len(datasets), 4)


def suite():
    """The test suite for test_viirs_l1b.
    """
    loader = unittest.TestLoader()
    mysuite = unittest.TestSuite()
    mysuite.addTest(loader.loadTestsFromTestCase(TestACSPOReader))

    return mysuite