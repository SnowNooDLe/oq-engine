# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2021 GEM Foundation
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
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Module exports :class:`FrankelEtAl1996MblgAB1987NSHMP2008`,
:class:`FrankelEtAl1996MblgJ1996NSHMP2008`,
:class:`FrankelEtAl1996MwNSHMP2008`.
"""
import numpy as np
from scipy.interpolate import RectBivariateSpline

from openquake.hazardlib.gsim.base import CoeffsTable, GMPE
from openquake.hazardlib.gsim.utils import (
    mblg_to_mw_atkinson_boore_87,
    mblg_to_mw_johnston_96,
    clip_mean)
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, SA


class FrankelEtAl1996MblgAB1987NSHMP2008(GMPE):
    """
    Implements GMPE developed by Arthur Frankel et al. and documented in
    "National Seismic-Hazard Maps: Documentation June 1996" (USGS - Open File
    Report 96-532) available at:
    http://earthquake.usgs.gov/hazards/products/conterminous/1996/documentation/ofr96-532.pdf

    The GMPE is used by the National Seismic Hazard Mapping Project (NSHMP) for
    the 2008 central and eastern US hazard model.

    This class replicates the algorithm as implemented in
    ``subroutine getFEA`` in the ``hazgridXnga2.f`` Fortran code available
    at: http://earthquake.usgs.gov/hazards/products/conterminous/2008/software/

    The GMPE is defined by a set of lookup tables (see Appendix A) defined
    from minimum magnitude Mw=4.4 to maximum magnitude Mw=8.2, and from
    (hypocentral) distance 10 km to 1000 km. Values outside these range
    are clipped.

    Lookup tables are defined for PGA, and SA at the following periods: 0.1,
    0.2, 0.3, 0.5, 1.0, 2.0. The GMPE does not allow for interpolation on
    unsupported periods.

    The class assumes rupture magnitude to be in Mblg scale (given that
    MFDs for central and eastern US are given in this scale). However lookup
    tables are defined for Mw. Therefore Mblg is converted to Mw by using
    Atkinson and Boore 1987 conversion equation.

    Coefficients are given for the B/C site conditions.
    """

    #: Supported tectonic region type is stable continental crust,
    #: given that the equations have been derived for central and eastern
    #: north America
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.STABLE_CONTINENTAL

    #: Supported intensity measure types are spectral acceleration,
    #: and peak ground acceleration
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGA,
        SA
    ])

    #: Supported intensity measure component is the geometric mean of
    #two : horizontal components
    #:attr:`~openquake.hazardlib.const.IMC.AVERAGE_HORIZONTAL`,
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation type is only total.
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: No site parameters required
    REQUIRES_SITES_PARAMETERS = set()

    #: Required rupture parameter is only magnitude (Mblg).
    REQUIRES_RUPTURE_PARAMETERS = {'mag'}

    #: Required distance measure is rhypo
    REQUIRES_DISTANCES = {'rhypo'}

    #: Shear-wave velocity for reference soil conditions in [m s-1]
    DEFINED_FOR_REFERENCE_VELOCITY = 760.

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.

        :raises ValueError:
            if imt is instance of :class:`openquake.hazardlib.imt.SA` with
            unsupported period.
        """
        assert all(stddev_type in self.DEFINED_FOR_STANDARD_DEVIATION_TYPES
                   for stddev_type in stddev_types)

        if imt not in self.IMTS_TABLES:
            raise ValueError(
                'IMT %s not supported in FrankelEtAl1996NSHMP. ' % repr(imt) +
                'FrankelEtAl1996NSHMP does not allow interpolation for ' +
                'unsupported periods.'
            )

        mean = self._compute_mean(imt, rup.mag, dists.rhypo.copy())
        mean = clip_mean(imt, mean)

        stddevs = self._compute_stddevs(imt, dists.rhypo.shape, stddev_types)

        return mean, stddevs

    def _compute_mean(self, imt, mag, rhypo):
        """
        Compute mean value from lookup table.

        Lookup table defines log10(IMT) (in g) for combinations of Mw and
        log10(rhypo) values. ``mag`` is therefore converted from Mblg to Mw
        using Atkinson and Boore 1987 conversion equation. Mean value is
        finally converted from base 10 to base e.
        """
        mag = np.zeros_like(rhypo) + self._convert_magnitude(mag)

        # to avoid run time warning in case rhypo is zero set minimum distance
        # to 10, which is anyhow the minimum distance allowed by the tables
        rhypo[rhypo < 10] = 10
        rhypo = np.log10(rhypo)

        # create lookup table and interpolate it at magnitude/distance values
        table = RectBivariateSpline(
            self.MAGS, self.DISTS, self.IMTS_TABLES[imt].T
        )
        mean = table.ev(mag, rhypo)

        # convert mean from base 10 to base e
        return mean * np.log(10)

    def _convert_magnitude(self, mag):
        """
        Convert magnitude from Mblg to Mw using Atkinson and Boore 1987
        equation
        """
        return mblg_to_mw_atkinson_boore_87(mag)

    def _compute_stddevs(self, imt, num_sites, stddev_types):
        """
        Return total standard deviation (converted to base e)
        """
        C = self.COEFFS[imt]

        stddevs = []
        for _ in stddev_types:
            stddevs.append(np.zeros(num_sites) + C['sigma'] * np.log(10))

        return stddevs

    # magnitude values for lookup table from minimum magnitude 4.4 to maximum
    # magnitude 8.2
    MAGS = np.linspace(4.4, 8.2, 20)

    # hypocentral distance values (log10) for lookup table
    # from minimum distance 10 km to maximum distance 1000 km
    DISTS = np.linspace(1., 3., 21)

    # lookup table for PGA
    PGA_TBL = np.array([
        [-0.71, -0.62, -0.53, -0.44, -0.36, -0.29, -0.21, -0.14, -0.07,  0.00,  0.06,  0.12,  0.19,  0.25,  0.31,  0.37,  0.43,  0.49,  0.54,  0.60],
        [-0.84, -0.75, -0.66, -0.57, -0.49, -0.41, -0.33, -0.26, -0.19, -0.12, -0.05,  0.01,  0.07,  0.14,  0.20,  0.26,  0.32,  0.38,  0.43,  0.49],
        [-0.98, -0.88, -0.79, -0.70, -0.62, -0.53, -0.46, -0.38, -0.31, -0.24, -0.17, -0.10, -0.04,  0.02,  0.08,  0.14,  0.20,  0.26,  0.32,  0.38],
        [-1.12, -1.02, -0.93, -0.84, -0.75, -0.66, -0.58, -0.51, -0.43, -0.36, -0.29, -0.22, -0.16, -0.10, -0.03,  0.03,  0.09,  0.15,  0.21,  0.27],
        [-1.27, -1.17, -1.07, -0.98, -0.89, -0.80, -0.72, -0.64, -0.56, -0.49, -0.42, -0.35, -0.28, -0.22, -0.15, -0.09, -0.03,  0.03,  0.09,  0.15],
        [-1.43, -1.32, -1.22, -1.13, -1.03, -0.94, -0.86, -0.78, -0.70, -0.62, -0.55, -0.48, -0.41, -0.34, -0.28, -0.22, -0.15, -0.09, -0.03,  0.03],
        [-1.59, -1.48, -1.38, -1.28, -1.19, -1.09, -1.01, -0.92, -0.84, -0.76, -0.69, -0.61, -0.54, -0.48, -0.41, -0.35, -0.28, -0.22, -0.16, -0.10],
        [-1.76, -1.65, -1.54, -1.44, -1.35, -1.25, -1.16, -1.07, -0.99, -0.91, -0.83, -0.76, -0.69, -0.62, -0.55, -0.48, -0.42, -0.35, -0.29, -0.23],
        [-1.93, -1.82, -1.72, -1.61, -1.51, -1.42, -1.33, -1.24, -1.15, -1.07, -0.99, -0.91, -0.83, -0.76, -0.69, -0.63, -0.56, -0.50, -0.43, -0.37],
        [-2.07, -1.95, -1.84, -1.74, -1.64, -1.54, -1.44, -1.35, -1.26, -1.18, -1.10, -1.02, -0.94, -0.86, -0.79, -0.72, -0.65, -0.59, -0.53, -0.46],
        [-2.17, -2.05, -1.94, -1.83, -1.73, -1.63, -1.53, -1.43, -1.34, -1.25, -1.17, -1.09, -1.01, -0.93, -0.86, -0.78, -0.71, -0.65, -0.58, -0.52],
        [-2.28, -2.16, -2.04, -1.93, -1.83, -1.72, -1.62, -1.53, -1.43, -1.34, -1.25, -1.17, -1.09, -1.01, -0.93, -0.86, -0.78, -0.71, -0.65, -0.58],
        [-2.44, -2.32, -2.20, -2.09, -1.98, -1.87, -1.77, -1.67, -1.58, -1.48, -1.39, -1.30, -1.22, -1.14, -1.06, -0.98, -0.91, -0.83, -0.77, -0.70],
        [-2.63, -2.50, -2.38, -2.26, -2.15, -2.04, -1.94, -1.84, -1.74, -1.64, -1.55, -1.46, -1.37, -1.29, -1.20, -1.12, -1.05, -0.97, -0.90, -0.83],
        [-2.83, -2.70, -2.57, -2.45, -2.34, -2.23, -2.12, -2.01, -1.91, -1.81, -1.72, -1.62, -1.53, -1.45, -1.36, -1.28, -1.20, -1.12, -1.05, -0.98],
        [-3.05, -2.92, -2.78, -2.66, -2.54, -2.42, -2.31, -2.20, -2.10, -2.00, -1.90, -1.80, -1.71, -1.62, -1.53, -1.45, -1.36, -1.28, -1.21, -1.13],
        [-3.29, -3.15, -3.01, -2.88, -2.75, -2.63, -2.52, -2.41, -2.30, -2.19, -2.09, -1.99, -1.90, -1.80, -1.71, -1.62, -1.54, -1.46, -1.38, -1.30],
        [-3.55, -3.40, -3.25, -3.11, -2.98, -2.86, -2.74, -2.62, -2.51, -2.40, -2.30, -2.19, -2.09, -2.00, -1.90, -1.81, -1.72, -1.64, -1.56, -1.48],
        [-3.84, -3.67, -3.52, -3.37, -3.23, -3.10, -2.97, -2.85, -2.73, -2.62, -2.51, -2.41, -2.30, -2.20, -2.10, -2.01, -1.92, -1.83, -1.74, -1.66],
        [-4.15, -3.97, -3.80, -3.65, -3.50, -3.36, -3.22, -3.09, -2.97, -2.85, -2.74, -2.63, -2.52, -2.42, -2.31, -2.22, -2.12, -2.03, -1.94, -1.85],
        [-4.48, -4.29, -4.11, -3.94, -3.78, -3.63, -3.49, -3.35, -3.22, -3.10, -2.98, -2.86, -2.75, -2.64, -2.53, -2.43, -2.33, -2.23, -2.14, -2.05]
    ])

    # lookup table for SA 0.1
    SA01_TBL = np.array([
        [-0.43, -0.32, -0.23, -0.14, -0.05,  0.03,  0.11,  0.19,  0.26,  0.33,  0.40,  0.47,  0.54,  0.60,  0.66,  0.72,  0.78,  0.84,  0.90,  0.96],
        [-0.55, -0.44, -0.35, -0.26, -0.17, -0.08,  0.00,  0.07,  0.15,  0.22,  0.29,  0.36,  0.43,  0.49,  0.55,  0.62,  0.68,  0.74,  0.80,  0.86],
        [-0.67, -0.57, -0.47, -0.38, -0.29, -0.20, -0.12, -0.04,  0.03,  0.11,  0.18,  0.25,  0.31,  0.38,  0.44,  0.51,  0.57,  0.63,  0.69,  0.75],
        [-0.80, -0.69, -0.60, -0.50, -0.41, -0.33, -0.24, -0.16, -0.09, -0.01,  0.06,  0.13,  0.20,  0.27,  0.33,  0.39,  0.46,  0.52,  0.58,  0.64],
        [-0.93, -0.83, -0.73, -0.63, -0.54, -0.45, -0.37, -0.29, -0.21, -0.13, -0.06,  0.01,  0.08,  0.15,  0.21,  0.28,  0.34,  0.40,  0.46,  0.52],
        [-1.07, -0.97, -0.86, -0.77, -0.68, -0.59, -0.50, -0.42, -0.34, -0.26, -0.18, -0.11, -0.04,  0.03,  0.09,  0.16,  0.22,  0.28,  0.35,  0.41],
        [-1.22, -1.11, -1.01, -0.91, -0.82, -0.73, -0.64, -0.55, -0.47, -0.39, -0.32, -0.24, -0.17, -0.10, -0.03,  0.03,  0.10,  0.16,  0.22,  0.28],
        [-1.37, -1.26, -1.16, -1.06, -0.97, -0.87, -0.78, -0.70, -0.61, -0.53, -0.45, -0.38, -0.30, -0.23, -0.16, -0.10, -0.03,  0.03,  0.10,  0.16],
        [-1.53, -1.42, -1.32, -1.22, -1.12, -1.03, -0.94, -0.85, -0.76, -0.68, -0.60, -0.52, -0.45, -0.37, -0.30, -0.23, -0.17, -0.10, -0.04,  0.02],
        [-1.65, -1.54, -1.43, -1.33, -1.24, -1.14, -1.05, -0.96, -0.87, -0.79, -0.70, -0.62, -0.54, -0.47, -0.40, -0.33, -0.26, -0.19, -0.13, -0.06],
        [-1.73, -1.62, -1.51, -1.41, -1.31, -1.22, -1.12, -1.03, -0.94, -0.86, -0.77, -0.69, -0.61, -0.53, -0.46, -0.39, -0.32, -0.25, -0.18, -0.12],
        [-1.83, -1.72, -1.61, -1.51, -1.41, -1.31, -1.21, -1.12, -1.03, -0.94, -0.85, -0.77, -0.69, -0.61, -0.53, -0.46, -0.39, -0.32, -0.25, -0.18],
        [-1.98, -1.87, -1.76, -1.66, -1.56, -1.46, -1.36, -1.27, -1.18, -1.09, -1.00, -0.91, -0.83, -0.75, -0.67, -0.59, -0.52, -0.44, -0.37, -0.31],
        [-2.17, -2.05, -1.95, -1.84, -1.74, -1.64, -1.54, -1.45, -1.35, -1.26, -1.17, -1.08, -0.99, -0.91, -0.83, -0.75, -0.67, -0.60, -0.53, -0.46],
        [-2.38, -2.26, -2.15, -2.05, -1.94, -1.84, -1.74, -1.64, -1.55, -1.45, -1.36, -1.27, -1.18, -1.10, -1.01, -0.93, -0.85, -0.78, -0.70, -0.63],
        [-2.61, -2.50, -2.39, -2.28, -2.17, -2.07, -1.97, -1.87, -1.77, -1.68, -1.58, -1.49, -1.40, -1.31, -1.22, -1.14, -1.06, -0.98, -0.91, -0.83],
        [-2.89, -2.77, -2.66, -2.55, -2.44, -2.33, -2.23, -2.13, -2.03, -1.93, -1.83, -1.74, -1.64, -1.55, -1.46, -1.38, -1.29, -1.21, -1.13, -1.06],
        [-3.20, -3.08, -2.96, -2.85, -2.73, -2.62, -2.51, -2.41, -2.31, -2.20, -2.10, -2.01, -1.91, -1.82, -1.72, -1.63, -1.55, -1.46, -1.38, -1.30],
        [-3.56, -3.43, -3.30, -3.18, -3.06, -2.94, -2.82, -2.71, -2.60, -2.49, -2.39, -2.29, -2.19, -2.09, -1.99, -1.90, -1.81, -1.72, -1.64, -1.56],
        [-3.96, -3.81, -3.67, -3.53, -3.39, -3.26, -3.14, -3.02, -2.90, -2.78, -2.67, -2.57, -2.46, -2.36, -2.26, -2.16, -2.07, -1.97, -1.88, -1.80],
        [-4.37, -4.20, -4.04, -3.88, -3.73, -3.59, -3.45, -3.32, -3.19, -3.07, -2.95, -2.83, -2.72, -2.61, -2.51, -2.40, -2.31, -2.21, -2.12, -2.03]
    ])

    # lookup table for SA 0.2
    SA02_TBL = np.array([
        [-0.71, -0.57, -0.46, -0.35, -0.25, -0.15, -0.06,  0.02,  0.10,  0.18,  0.25,  0.32,  0.39,  0.46,  0.53,  0.59,  0.65,  0.72,  0.78,  0.84],
        [-0.82, -0.69, -0.57, -0.46, -0.36, -0.26, -0.17, -0.09, -0.01,  0.07,  0.14,  0.22,  0.29,  0.35,  0.42,  0.48,  0.55,  0.61,  0.67,  0.73],
        [-0.93, -0.80, -0.68, -0.57, -0.47, -0.38, -0.29, -0.20, -0.12, -0.04,  0.03,  0.11,  0.18,  0.25,  0.31,  0.38,  0.44,  0.50,  0.56,  0.63],
        [-1.05, -0.92, -0.80, -0.69, -0.59, -0.49, -0.40, -0.32, -0.23, -0.15, -0.08,  0.00,  0.07,  0.14,  0.20,  0.27,  0.33,  0.40,  0.46,  0.52],
        [-1.17, -1.04, -0.92, -0.81, -0.71, -0.61, -0.52, -0.44, -0.35, -0.27, -0.19, -0.12, -0.05,  0.02,  0.09,  0.16,  0.22,  0.29,  0.35,  0.41],
        [-1.30, -1.17, -1.05, -0.94, -0.84, -0.74, -0.65, -0.56, -0.47, -0.39, -0.31, -0.24, -0.16, -0.09, -0.02,  0.04,  0.11,  0.17,  0.24,  0.30],
        [-1.43, -1.30, -1.18, -1.07, -0.97, -0.87, -0.77, -0.69, -0.60, -0.52, -0.44, -0.36, -0.28, -0.21, -0.14, -0.07, -0.01,  0.06,  0.12,  0.18],
        [-1.57, -1.44, -1.32, -1.21, -1.10, -1.00, -0.91, -0.82, -0.73, -0.65, -0.56, -0.49, -0.41, -0.34, -0.27, -0.20, -0.13, -0.06,  0.00,  0.06],
        [-1.72, -1.58, -1.46, -1.35, -1.25, -1.15, -1.05, -0.96, -0.87, -0.78, -0.70, -0.62, -0.54, -0.47, -0.39, -0.32, -0.25, -0.19, -0.12, -0.06],
        [-1.82, -1.68, -1.56, -1.45, -1.34, -1.24, -1.14, -1.05, -0.96, -0.87, -0.79, -0.70, -0.63, -0.55, -0.47, -0.40, -0.33, -0.26, -0.20, -0.13],
        [-1.88, -1.74, -1.62, -1.51, -1.40, -1.30, -1.20, -1.10, -1.01, -0.92, -0.84, -0.75, -0.67, -0.59, -0.52, -0.44, -0.37, -0.30, -0.24, -0.17],
        [-1.95, -1.82, -1.69, -1.58, -1.47, -1.37, -1.27, -1.17, -1.08, -0.99, -0.90, -0.81, -0.73, -0.65, -0.57, -0.50, -0.42, -0.35, -0.28, -0.22],
        [-2.08, -1.94, -1.82, -1.70, -1.59, -1.49, -1.39, -1.29, -1.20, -1.11, -1.02, -0.93, -0.84, -0.76, -0.68, -0.60, -0.53, -0.45, -0.38, -0.32],
        [-2.23, -2.09, -1.97, -1.85, -1.74, -1.64, -1.53, -1.44, -1.34, -1.25, -1.15, -1.06, -0.98, -0.89, -0.81, -0.73, -0.65, -0.58, -0.51, -0.44],
        [-2.40, -2.26, -2.13, -2.01, -1.90, -1.80, -1.70, -1.60, -1.50, -1.40, -1.31, -1.22, -1.13, -1.04, -0.96, -0.88, -0.80, -0.72, -0.65, -0.58],
        [-2.58, -2.44, -2.32, -2.20, -2.09, -1.98, -1.88, -1.78, -1.68, -1.58, -1.49, -1.39, -1.30, -1.22, -1.13, -1.04, -0.96, -0.88, -0.81, -0.73],
        [-2.80, -2.66, -2.53, -2.41, -2.30, -2.19, -2.09, -1.98, -1.88, -1.79, -1.69, -1.60, -1.50, -1.41, -1.32, -1.24, -1.15, -1.07, -0.99, -0.92],
        [-3.04, -2.90, -2.77, -2.65, -2.54, -2.43, -2.32, -2.22, -2.12, -2.02, -1.92, -1.83, -1.73, -1.64, -1.55, -1.46, -1.37, -1.29, -1.21, -1.13],
        [-3.33, -3.19, -3.06, -2.93, -2.82, -2.71, -2.60, -2.49, -2.39, -2.29, -2.19, -2.09, -1.99, -1.90, -1.80, -1.71, -1.62, -1.54, -1.45, -1.37],
        [-3.66, -3.52, -3.38, -3.26, -3.14, -3.02, -2.91, -2.80, -2.69, -2.59, -2.48, -2.38, -2.28, -2.18, -2.09, -1.99, -1.90, -1.81, -1.73, -1.64],
        [-4.05, -3.90, -3.76, -3.63, -3.50, -3.38, -3.26, -3.14, -3.03, -2.92, -2.81, -2.70, -2.59, -2.49, -2.39, -2.29, -2.19, -2.10, -2.01, -1.92]
    ])

    # lookup table for SA 0.3
    SA03_TBL = np.array([
        [-0.97, -0.81, -0.66, -0.53, -0.42, -0.31, -0.21, -0.12, -0.03,  0.05,  0.13,  0.20,  0.28,  0.35,  0.41,  0.48,  0.54,  0.61,  0.67,  0.73],
        [-1.08, -0.91, -0.77, -0.64, -0.53, -0.42, -0.32, -0.23, -0.14, -0.06,  0.02,  0.10,  0.17,  0.24,  0.31,  0.38,  0.44,  0.50,  0.57,  0.63],
        [-1.19, -1.02, -0.88, -0.75, -0.64, -0.53, -0.43, -0.34, -0.25, -0.17, -0.09, -0.01,  0.06,  0.13,  0.20,  0.27,  0.33,  0.40,  0.46,  0.52],
        [-1.30, -1.14, -0.99, -0.86, -0.75, -0.64, -0.54, -0.45, -0.36, -0.28, -0.20, -0.12, -0.05,  0.03,  0.09,  0.16,  0.23,  0.29,  0.36,  0.42],
        [-1.41, -1.25, -1.11, -0.98, -0.86, -0.76, -0.66, -0.57, -0.48, -0.39, -0.31, -0.23, -0.16, -0.09, -0.02,  0.05,  0.12,  0.18,  0.25,  0.31],
        [-1.53, -1.37, -1.23, -1.10, -0.98, -0.88, -0.78, -0.68, -0.59, -0.51, -0.43, -0.35, -0.27, -0.20, -0.13, -0.06,  0.01,  0.07,  0.14,  0.20],
        [-1.66, -1.50, -1.35, -1.23, -1.11, -1.00, -0.90, -0.81, -0.72, -0.63, -0.55, -0.47, -0.39, -0.31, -0.24, -0.17, -0.11, -0.04,  0.02,  0.09],
        [-1.79, -1.63, -1.48, -1.36, -1.24, -1.13, -1.03, -0.93, -0.84, -0.75, -0.67, -0.59, -0.51, -0.44, -0.36, -0.29, -0.22, -0.16, -0.09, -0.03],
        [-1.93, -1.77, -1.62, -1.49, -1.37, -1.26, -1.16, -1.07, -0.97, -0.88, -0.80, -0.72, -0.64, -0.56, -0.49, -0.41, -0.34, -0.28, -0.21, -0.15],
        [-2.02, -1.85, -1.71, -1.58, -1.46, -1.35, -1.25, -1.15, -1.06, -0.97, -0.88, -0.80, -0.71, -0.64, -0.56, -0.49, -0.42, -0.35, -0.28, -0.21],
        [-2.07, -1.91, -1.76, -1.63, -1.51, -1.40, -1.30, -1.20, -1.10, -1.01, -0.92, -0.84, -0.75, -0.67, -0.60, -0.52, -0.45, -0.38, -0.31, -0.24],
        [-2.13, -1.97, -1.82, -1.69, -1.57, -1.46, -1.35, -1.25, -1.16, -1.06, -0.97, -0.89, -0.80, -0.72, -0.64, -0.56, -0.49, -0.42, -0.35, -0.28],
        [-2.25, -2.08, -1.93, -1.80, -1.68, -1.57, -1.46, -1.36, -1.26, -1.17, -1.08, -0.99, -0.90, -0.82, -0.74, -0.66, -0.58, -0.51, -0.44, -0.37],
        [-2.38, -2.21, -2.06, -1.93, -1.81, -1.70, -1.59, -1.49, -1.39, -1.29, -1.20, -1.11, -1.02, -0.94, -0.85, -0.77, -0.70, -0.62, -0.55, -0.48],
        [-2.53, -2.36, -2.21, -2.08, -1.96, -1.84, -1.73, -1.63, -1.53, -1.43, -1.34, -1.25, -1.16, -1.07, -0.99, -0.90, -0.82, -0.75, -0.67, -0.60],
        [-2.69, -2.52, -2.37, -2.24, -2.12, -2.00, -1.89, -1.79, -1.69, -1.59, -1.50, -1.40, -1.31, -1.22, -1.13, -1.05, -0.97, -0.89, -0.81, -0.74],
        [-2.88, -2.71, -2.56, -2.42, -2.30, -2.18, -2.08, -1.97, -1.87, -1.77, -1.67, -1.58, -1.48, -1.39, -1.30, -1.22, -1.13, -1.05, -0.97, -0.90],
        [-3.09, -2.92, -2.77, -2.63, -2.51, -2.39, -2.28, -2.18, -2.07, -1.97, -1.87, -1.78, -1.68, -1.59, -1.50, -1.41, -1.32, -1.24, -1.16, -1.08],
        [-3.33, -3.16, -3.01, -2.87, -2.75, -2.63, -2.52, -2.41, -2.31, -2.20, -2.11, -2.01, -1.91, -1.82, -1.72, -1.63, -1.54, -1.46, -1.37, -1.29],
        [-3.61, -3.44, -3.29, -3.15, -3.02, -2.91, -2.79, -2.68, -2.58, -2.47, -2.37, -2.27, -2.17, -2.08, -1.98, -1.89, -1.80, -1.71, -1.62, -1.54],
        [-3.95, -3.77, -3.62, -3.48, -3.35, -3.22, -3.11, -3.00, -2.89, -2.78, -2.67, -2.57, -2.47, -2.37, -2.27, -2.17, -2.08, -1.99, -1.90, -1.81]
    ])

    # lookup table for SA 0.5
    SA05_TBL = np.array([
        [-1.44, -1.23, -1.03, -0.87, -0.72, -0.58, -0.46, -0.35, -0.25, -0.16, -0.07,  0.01,  0.09,  0.16,  0.23,  0.30,  0.37,  0.44,  0.50,  0.57],
        [-1.54, -1.33, -1.14, -0.97, -0.82, -0.69, -0.57, -0.46, -0.36, -0.27, -0.18, -0.10, -0.02,  0.06,  0.13,  0.20,  0.27,  0.34,  0.40,  0.46],
        [-1.64, -1.43, -1.24, -1.07, -0.92, -0.79, -0.67, -0.57, -0.47, -0.37, -0.29, -0.20, -0.12, -0.05,  0.03,  0.10,  0.16,  0.23,  0.30,  0.36],
        [-1.74, -1.53, -1.35, -1.18, -1.03, -0.90, -0.78, -0.67, -0.57, -0.48, -0.39, -0.31, -0.23, -0.15, -0.08, -0.01,  0.06,  0.13,  0.19,  0.26],
        [-1.85, -1.64, -1.46, -1.29, -1.14, -1.01, -0.89, -0.79, -0.69, -0.59, -0.50, -0.42, -0.34, -0.26, -0.19, -0.12, -0.05,  0.02,  0.09,  0.15],
        [-1.96, -1.75, -1.57, -1.40, -1.25, -1.12, -1.01, -0.90, -0.80, -0.70, -0.62, -0.53, -0.45, -0.37, -0.30, -0.23, -0.16, -0.09, -0.02,  0.04],
        [-2.08, -1.87, -1.68, -1.52, -1.37, -1.24, -1.12, -1.02, -0.91, -0.82, -0.73, -0.65, -0.56, -0.49, -0.41, -0.34, -0.27, -0.20, -0.13, -0.07],
        [-2.20, -1.99, -1.81, -1.64, -1.49, -1.36, -1.24, -1.14, -1.03, -0.94, -0.85, -0.76, -0.68, -0.60, -0.53, -0.45, -0.38, -0.31, -0.24, -0.18],
        [-2.33, -2.12, -1.93, -1.77, -1.62, -1.49, -1.37, -1.26, -1.16, -1.06, -0.97, -0.89, -0.80, -0.72, -0.64, -0.57, -0.50, -0.43, -0.36, -0.29],
        [-2.41, -2.20, -2.01, -1.84, -1.70, -1.56, -1.45, -1.34, -1.23, -1.14, -1.04, -0.96, -0.87, -0.79, -0.71, -0.64, -0.56, -0.49, -0.42, -0.36],
        [-2.45, -2.24, -2.05, -1.88, -1.73, -1.60, -1.48, -1.37, -1.27, -1.17, -1.08, -0.99, -0.90, -0.82, -0.74, -0.66, -0.59, -0.52, -0.45, -0.38],
        [-2.49, -2.28, -2.10, -1.93, -1.78, -1.65, -1.53, -1.42, -1.31, -1.21, -1.12, -1.03, -0.94, -0.86, -0.78, -0.70, -0.62, -0.55, -0.48, -0.41],
        [-2.59, -2.38, -2.19, -2.03, -1.88, -1.74, -1.62, -1.51, -1.41, -1.31, -1.21, -1.12, -1.03, -0.94, -0.86, -0.78, -0.70, -0.63, -0.56, -0.49],
        [-2.71, -2.50, -2.31, -2.14, -1.99, -1.86, -1.74, -1.62, -1.52, -1.42, -1.32, -1.23, -1.14, -1.05, -0.96, -0.88, -0.80, -0.73, -0.65, -0.58],
        [-2.84, -2.63, -2.44, -2.27, -2.12, -1.98, -1.86, -1.75, -1.64, -1.54, -1.44, -1.34, -1.25, -1.16, -1.08, -0.99, -0.91, -0.83, -0.76, -0.68],
        [-2.98, -2.77, -2.58, -2.41, -2.26, -2.12, -2.00, -1.88, -1.77, -1.67, -1.57, -1.48, -1.38, -1.29, -1.20, -1.12, -1.04, -0.96, -0.88, -0.80],
        [-3.14, -2.92, -2.73, -2.56, -2.41, -2.27, -2.15, -2.04, -1.93, -1.82, -1.72, -1.63, -1.53, -1.44, -1.35, -1.26, -1.18, -1.09, -1.01, -0.94],
        [-3.32, -3.10, -2.91, -2.74, -2.59, -2.45, -2.32, -2.21, -2.10, -1.99, -1.89, -1.79, -1.70, -1.60, -1.51, -1.42, -1.34, -1.25, -1.17, -1.09],
        [-3.52, -3.30, -3.11, -2.94, -2.78, -2.65, -2.52, -2.40, -2.29, -2.19, -2.08, -1.98, -1.89, -1.79, -1.70, -1.61, -1.52, -1.43, -1.35, -1.26],
        [-3.75, -3.53, -3.34, -3.17, -3.01, -2.87, -2.75, -2.63, -2.52, -2.41, -2.31, -2.20, -2.11, -2.01, -1.91, -1.82, -1.73, -1.64, -1.55, -1.47],
        [-4.02, -3.80, -3.60, -3.43, -3.27, -3.13, -3.01, -2.89, -2.77, -2.67, -2.56, -2.46, -2.36, -2.26, -2.16, -2.07, -1.97, -1.88, -1.79, -1.70],
    ])

    # lookup table for SA 1.0
    SA1_TBL = np.array([
        [-2.22, -1.98, -1.75, -1.52, -1.31, -1.12, -0.95, -0.80, -0.66, -0.54, -0.43, -0.33, -0.24, -0.15, -0.07,  0.01,  0.08,  0.16,  0.23,  0.29],
        [-2.32, -2.08, -1.85, -1.62, -1.41, -1.22, -1.05, -0.90, -0.77, -0.64, -0.54, -0.43, -0.34, -0.25, -0.17, -0.09, -0.02,  0.05,  0.12,  0.19],
        [-2.43, -2.18, -1.95, -1.72, -1.51, -1.32, -1.15, -1.00, -0.87, -0.75, -0.64, -0.54, -0.45, -0.36, -0.28, -0.20, -0.12, -0.05,  0.02,  0.09],
        [-2.53, -2.29, -2.05, -1.82, -1.61, -1.42, -1.25, -1.11, -0.97, -0.85, -0.74, -0.64, -0.55, -0.46, -0.38, -0.30, -0.23, -0.15, -0.08, -0.01],
        [-2.63, -2.39, -2.15, -1.92, -1.71, -1.53, -1.36, -1.21, -1.08, -0.96, -0.85, -0.75, -0.66, -0.57, -0.49, -0.41, -0.33, -0.26, -0.19, -0.12],
        [-2.74, -2.49, -2.25, -2.03, -1.82, -1.63, -1.46, -1.32, -1.18, -1.06, -0.96, -0.86, -0.76, -0.68, -0.59, -0.51, -0.44, -0.36, -0.29, -0.22],
        [-2.84, -2.60, -2.36, -2.13, -1.92, -1.74, -1.57, -1.42, -1.29, -1.17, -1.07, -0.97, -0.87, -0.78, -0.70, -0.62, -0.54, -0.47, -0.40, -0.33],
        [-2.95, -2.70, -2.47, -2.24, -2.03, -1.85, -1.68, -1.53, -1.40, -1.29, -1.18, -1.08, -0.98, -0.90, -0.81, -0.73, -0.65, -0.58, -0.51, -0.44],
        [-3.07, -2.82, -2.58, -2.35, -2.15, -1.96, -1.80, -1.65, -1.52, -1.40, -1.29, -1.19, -1.10, -1.01, -0.92, -0.84, -0.77, -0.69, -0.62, -0.55],
        [-3.14, -2.88, -2.64, -2.42, -2.21, -2.02, -1.86, -1.71, -1.58, -1.46, -1.36, -1.26, -1.16, -1.07, -0.99, -0.90, -0.83, -0.75, -0.68, -0.61],
        [-3.16, -2.91, -2.67, -2.44, -2.24, -2.05, -1.88, -1.74, -1.61, -1.49, -1.38, -1.28, -1.18, -1.09, -1.01, -0.92, -0.84, -0.77, -0.69, -0.62],
        [-3.20, -2.94, -2.70, -2.47, -2.27, -2.08, -1.91, -1.77, -1.63, -1.52, -1.41, -1.31, -1.21, -1.12, -1.03, -0.95, -0.87, -0.79, -0.71, -0.64],
        [-3.28, -3.03, -2.78, -2.55, -2.35, -2.16, -1.99, -1.84, -1.71, -1.59, -1.48, -1.38, -1.29, -1.19, -1.10, -1.02, -0.94, -0.86, -0.78, -0.71],
        [-3.38, -3.12, -2.88, -2.65, -2.44, -2.25, -2.09, -1.94, -1.81, -1.69, -1.58, -1.47, -1.37, -1.28, -1.19, -1.11, -1.02, -0.94, -0.87, -0.79],
        [-3.49, -3.23, -2.98, -2.75, -2.55, -2.36, -2.19, -2.04, -1.91, -1.79, -1.68, -1.57, -1.47, -1.38, -1.29, -1.20, -1.12, -1.03, -0.96, -0.88],
        [-3.61, -3.35, -3.10, -2.87, -2.66, -2.47, -2.30, -2.15, -2.02, -1.90, -1.79, -1.68, -1.58, -1.49, -1.39, -1.30, -1.22, -1.14, -1.05, -0.98],
        [-3.74, -3.48, -3.23, -3.00, -2.79, -2.60, -2.43, -2.28, -2.14, -2.02, -1.91, -1.80, -1.70, -1.60, -1.51, -1.42, -1.33, -1.25, -1.16, -1.09],
        [-3.88, -3.62, -3.37, -3.14, -2.93, -2.74, -2.57, -2.41, -2.28, -2.16, -2.04, -1.94, -1.83, -1.74, -1.64, -1.55, -1.46, -1.37, -1.29, -1.21],
        [-4.04, -3.78, -3.53, -3.30, -3.08, -2.89, -2.72, -2.57, -2.43, -2.31, -2.20, -2.09, -1.98, -1.88, -1.79, -1.69, -1.60, -1.51, -1.43, -1.35],
        [-4.22, -3.96, -3.71, -3.47, -3.26, -3.07, -2.90, -2.74, -2.61, -2.48, -2.37, -2.26, -2.15, -2.05, -1.96, -1.86, -1.77, -1.68, -1.59, -1.50],
        [-4.43, -4.16, -3.91, -3.68, -3.46, -3.27, -3.10, -2.94, -2.81, -2.68, -2.56, -2.45, -2.35, -2.25, -2.15, -2.05, -1.95, -1.86, -1.77, -1.69]
    ])

    # lookup table for SA 2.0
    SA2_TBL = np.array([
        [-2.87, -2.66, -2.45, -2.24, -2.03, -1.81, -1.60, -1.39, -1.20, -1.02, -0.87, -0.73, -0.61, -0.50, -0.40, -0.30, -0.21, -0.13, -0.05,  0.02],
        [-3.00, -2.78, -2.57, -2.36, -2.14, -1.92, -1.70, -1.49, -1.30, -1.12, -0.97, -0.83, -0.71, -0.60, -0.50, -0.40, -0.32, -0.23, -0.16, -0.08],
        [-3.14, -2.91, -2.69, -2.47, -2.24, -2.02, -1.80, -1.59, -1.40, -1.22, -1.07, -0.93, -0.81, -0.70, -0.60, -0.51, -0.42, -0.34, -0.26, -0.18],
        [-3.27, -3.04, -2.81, -2.58, -2.35, -2.12, -1.90, -1.69, -1.50, -1.32, -1.17, -1.04, -0.91, -0.80, -0.70, -0.61, -0.52, -0.44, -0.36, -0.28],
        [-3.40, -3.16, -2.92, -2.69, -2.45, -2.22, -2.00, -1.79, -1.60, -1.43, -1.27, -1.14, -1.02, -0.91, -0.81, -0.71, -0.62, -0.54, -0.46, -0.39],
        [-3.52, -3.28, -3.03, -2.79, -2.55, -2.32, -2.10, -1.89, -1.70, -1.53, -1.38, -1.24, -1.12, -1.01, -0.91, -0.82, -0.73, -0.65, -0.57, -0.49],
        [-3.64, -3.39, -3.14, -2.90, -2.66, -2.42, -2.20, -1.99, -1.80, -1.63, -1.48, -1.35, -1.22, -1.12, -1.02, -0.92, -0.83, -0.75, -0.67, -0.60],
        [-3.76, -3.50, -3.25, -3.00, -2.76, -2.52, -2.30, -2.09, -1.90, -1.73, -1.58, -1.45, -1.33, -1.22, -1.12, -1.03, -0.94, -0.86, -0.78, -0.70],
        [-3.87, -3.61, -3.36, -3.11, -2.86, -2.63, -2.40, -2.19, -2.01, -1.84, -1.69, -1.56, -1.44, -1.33, -1.23, -1.14, -1.05, -0.96, -0.89, -0.81],
        [-3.93, -3.67, -3.42, -3.16, -2.92, -2.68, -2.45, -2.25, -2.06, -1.89, -1.75, -1.61, -1.49, -1.39, -1.29, -1.19, -1.10, -1.02, -0.94, -0.86],
        [-3.95, -3.69, -3.43, -3.18, -2.93, -2.69, -2.47, -2.26, -2.07, -1.90, -1.76, -1.63, -1.51, -1.40, -1.30, -1.20, -1.12, -1.03, -0.95, -0.87],
        [-3.97, -3.71, -3.45, -3.20, -2.95, -2.71, -2.48, -2.27, -2.09, -1.92, -1.77, -1.64, -1.52, -1.42, -1.32, -1.22, -1.13, -1.05, -0.97, -0.89],
        [-4.05, -3.78, -3.52, -3.26, -3.01, -2.77, -2.55, -2.34, -2.15, -1.99, -1.84, -1.71, -1.59, -1.48, -1.38, -1.28, -1.19, -1.11, -1.03, -0.95],
        [-4.14, -3.87, -3.60, -3.34, -3.09, -2.85, -2.62, -2.42, -2.23, -2.06, -1.91, -1.78, -1.66, -1.56, -1.45, -1.36, -1.27, -1.18, -1.10, -1.02],
        [-4.23, -3.96, -3.69, -3.43, -3.18, -2.94, -2.71, -2.50, -2.31, -2.15, -2.00, -1.87, -1.75, -1.64, -1.54, -1.44, -1.35, -1.26, -1.18, -1.10],
        [-4.34, -4.06, -3.79, -3.53, -3.27, -3.03, -2.80, -2.59, -2.40, -2.24, -2.09, -1.96, -1.84, -1.73, -1.62, -1.53, -1.44, -1.35, -1.26, -1.18],
        [-4.45, -4.18, -3.90, -3.64, -3.38, -3.13, -2.90, -2.69, -2.51, -2.34, -2.19, -2.06, -1.94, -1.83, -1.72, -1.62, -1.53, -1.44, -1.35, -1.27],
        [-4.58, -4.30, -4.02, -3.75, -3.49, -3.25, -3.02, -2.81, -2.62, -2.45, -2.30, -2.17, -2.04, -1.93, -1.83, -1.73, -1.63, -1.54, -1.46, -1.37],
        [-4.71, -4.43, -4.15, -3.88, -3.62, -3.37, -3.14, -2.93, -2.74, -2.57, -2.42, -2.29, -2.17, -2.05, -1.95, -1.85, -1.75, -1.66, -1.57, -1.48],
        [-4.86, -4.58, -4.30, -4.03, -3.76, -3.51, -3.28, -3.07, -2.88, -2.71, -2.56, -2.42, -2.30, -2.19, -2.08, -1.98, -1.88, -1.79, -1.70, -1.61],
        [-5.03, -4.74, -4.46, -4.19, -3.92, -3.67, -3.44, -3.23, -3.03, -2.86, -2.71, -2.58, -2.45, -2.34, -2.23, -2.13, -2.03, -1.93, -1.84, -1.75]
    ])

    # dictionary relating supported imts and associated tables
    IMTS_TABLES = {
        PGA(): PGA_TBL,
        SA(0.1): SA01_TBL,
        SA(0.2): SA02_TBL,
        SA(0.3): SA03_TBL,
        SA(0.5): SA05_TBL,
        SA(1.0): SA1_TBL,
        SA(2.0): SA2_TBL
    }

    # period dependent standard deviations (in base 10)
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    IMT    sigma
    pga    0.326
    0.1    0.326
    0.2    0.326
    0.3    0.326
    0.5    0.326
    1.0    0.347
    2.0    0.347
    """)


class FrankelEtAl1996MblgJ1996NSHMP2008(FrankelEtAl1996MblgAB1987NSHMP2008):
    """
    Extend :class:`FrankelEtAl1996MblgAB1987NSHMP2008` but uses Johnston
    1996 equation for converting from Mblg to Mw.
    """
    def _convert_magnitude(self, mag):
        """
        Convert magnitude from Mblg to Mw using Johnston 1996 equation
        """
        return mblg_to_mw_johnston_96(mag)


class FrankelEtAl1996MwNSHMP2008(FrankelEtAl1996MblgAB1987NSHMP2008):
    """
    Extend :class:`FrankelEtAl1996MblgAB1987NSHMP2008` but assumes magnitude
    to be in Mw scale and therefore no conversion is applied.
    """
    def _convert_magnitude(self, mag):
        """
        Return magnitude value unchanged
        """
        return mag
