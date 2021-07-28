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
import numpy as np
import pandas as pd

from openquake.baselib.hdf5 import read_csv
from openquake.hazardlib.imt import from_string
from openquake.hazardlib.contexts import ContextMaker
from openquake.hazardlib.tests.gsim.check_gsim import check_gsim


def get_out_types(stdtypes):
    out = ["MEAN"]
    for stdtype in sorted(stdtypes):
        upper = stdtype.upper().replace(' ', '_')
        out.append(upper + '_STDDEV')
    return out


def all_equals(inputs):
    inp0 = inputs[0]
    for inp in inputs[1:]:
        diff = inp != inp0
        if isinstance(diff, np.ndarray):
            if diff.any():
                return False
        elif diff:
            return False
    return True


def verify(gsim, pathnames, ptol1, ptol2):
    """
    Verify the gsim by using the verification tables within the given
    tolerances
    """
    cmaker = ContextMaker(gsim.DEFINED_FOR_TECTONIC_REGION_TYPE, [gsim])
    out_types = get_out_types(gsim.DEFINED_FOR_STANDARD_DEVIATION_TYPES)
    assert len(out_types) == len(pathnames)
    result = {}  # out_type -> mean or std
    inputs = []
    outfields = []
    for path in pathnames:
        df = pd.read_csv(path)
        arr = df.to_numpy()
        idx = list(df.columns).index('result_type')
        [out_type] = df.result_type.unique()
        result[out_type] = arr[:, idx + 2:]
        inpfields = list(df.columns[:idx])
        inputs.append(arr[:, :idx])
        outfields.append(df.columns[idx + 2:].to_numpy())
        # all fields except result_type, damping, i.e. the IMT fields
    pnames = ' '.join(pathnames)
    assert all_equals(inputs), 'Inconsistent inputs in %s' % pnames
    assert all_equals(outfields), 'Inconsistent IMTs in %s' % pnames
    imts = [from_string(f.strip().upper()) for f in outfields[0]]
    C = len(inputs[0])
    ctx = cmaker.ctx_builder.zeros(C).view(np.recarray)
    for i, inpfield in enumerate(inpfields):
        # ex. inpfields = ['rup_mag', 'rup_rake', 'dist_rjb', 'site_vs30']
        prefix, suffix = inpfield.split('_')
        setattr(ctx, suffix, inputs[0][:, i])
    out = np.zeros((4, C))
    gsim.compute(ctx, imts, *out)
    idx = dict(
        MEAN=0, TOTAL_STDDEV=1, INTER_EVENT_STDDEV=2, INTRA_EVENT_STDDEV=3)
    for m, imt in enumerate(imts):
        for result_type, res in result.items():
            np.testing.assert_allclose(out[idx[result_type], m], res[:, m])


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
