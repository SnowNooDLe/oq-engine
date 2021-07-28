# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2012-2021 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.
import unittest
import os

from openquake.baselib.hdf5 import read_csv
from openquake.hazardlib.tests.gsim.check_gsim import check_gsim


def get_out_types(stdtypes):
    out = ["MEAN"]
    for stdtype in sorted(stdtypes):
        upper = stdtype.upper().replace(' ', '_')
        out.append(upper + '_STDDEV')
    return out


def verify(gsim, pathnames, ptol1, ptol2):
    """
    Verify the gsim by using the verification tables within the given
    tolerances
    """
    out_types = get_out_types(gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES)
    assert len(out_types) == len(pathnames)
    for path in pathnames:
        aw = read_csv(path, {'result_type': str, None: float})
        import pdb; pdb.set_trace()
    

class BaseGSIMTestCase(unittest.TestCase):
    BASE_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
    GSIM_CLASS = None

    def check(self, filename, max_discrep_percentage, **kwargs):
        gsim = self.GSIM_CLASS(**kwargs)
        with open(os.path.join(self.BASE_DATA_PATH, filename)) as f:
            errors, stats = check_gsim(gsim, f, max_discrep_percentage)
        if errors:
            raise AssertionError(stats)
        print()
        print(stats)

    def check_all(self, filenames, ptol1, ptol2=None, **kwargs):
        """
        :param filenames: list of local file names for the verification tables
        :param ptol1: tolerance (in percentage) for the mean
        :param ptol2: tolerance (in percentage) for the mean
        :param kwargs: parameters to pass to the GSIM_CLASS
        """
        gsim = self.GSIM_CLASS(**kwargs)
        fnames = [os.path.join(self.BASE_DATA_PATH, f) for f in filenames]
        verify(gsim, fnames, ptol1, ptol2 or ptol1)
