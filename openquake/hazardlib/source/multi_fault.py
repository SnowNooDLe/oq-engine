# The Hazard Library
# Copyright (C) 2012-2022 GEM Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Module :mod:`openquake.hazardlib.source.multi_fault`
defines :class:`MultiFaultSource`.
"""

import numpy as np
from typing import Union

from openquake.baselib.general import gen_slices
from openquake.hazardlib.source.rupture import (
    NonParametricProbabilisticRupture)
from openquake.hazardlib.source.non_parametric import (
    NonParametricSeismicSource as NP)
from openquake.hazardlib.geo.surface.multi import MultiSurface
from openquake.hazardlib.geo.utils import angular_distance, KM_TO_DEGREES
from openquake.hazardlib.source.base import BaseSeismicSource

F32 = np.float32
BLOCKSIZE = 1000
# the BLOCKSIZE has to be large to reduce the number of sources and
# therefore the redundant data transfer in the .sections attribute


class FaultSection(object):
    """
    A class to define a fault section, that is the geometry definition of a
    portion of a fault.

    :param sec_id:
        A unique identifier
    :param surface:
        An instance of
        :class:`openquake.hazardlib.geo.surface.base.BaseSurface` which
        describes the 3D geometry of a part of a fault system.
    """

    def __init__(self, sec_id: str, surface):
        self.sec_id = sec_id
        self.surface = surface

    def geom(self):
        """
        :returns:
            an array of float32 with structure
            [1., shape_y, shape_z, coords, ...]
        """
        shape_y, shape_z = self.surface.mesh.array.shape[1:]
        coords = F32(self.surface.mesh.array.flat)
        return np.concatenate([F32([1, shape_y, shape_z]), coords])


class MultiFaultSource(BaseSeismicSource):
    """
    The multi-fault source is a source typology specifiically support the
    calculation of hazard using fault models with segments participating to
    multiple ruptures.

    :param source_id:
        A unique identifier for the source
    :param name:
        The name of the fault
    :param tectonic_region_type:
        A string that defines the TRT of the fault source
    :param sections:
        A list of :class:`openquake.hazardlib.source.multi_fault.FaultSection`
        instances. The cardinality of this list is N.
    :param rupture_idxs:
        A list of lists. Each element contains the IDs of the sections
        participating to a rupture. The cardinality of this list is N.
    :param occurrence_probs:
        A list with cardinality N with instances of the class
        :class:`openquake.hazardlib.pmf.PMF`. Each element specifies the
        occurrence of 0, 1 ... occurrences of a rupture in the investigation
        time.
    :param magnitudes:
        An iterable with cardinality N containing the magnitudes of the
        ruptures
    :param rakes:
        An iterable with cardinality N containing the rake of each
        rupture
    """
    code = b'F'
    MODIFICATIONS = {}

    def __init__(self, source_id: str, name: str, tectonic_region_type: str,
                 rupture_idxs: list, occurrence_probs: Union[list, np.ndarray],
                 magnitudes: list, rakes: list):
        nrups = len(rupture_idxs)
        assert len(occurrence_probs) == len(magnitudes) == len(rakes) == nrups
        self.rupture_idxs = rupture_idxs
        self.pmfs = occurrence_probs
        self.mags = magnitudes
        self.rakes = rakes
        super().__init__(source_id, name, tectonic_region_type)

    def set_sections(self, sections):
        """
        :param sections: a dictionary sec_id -> FaultSection

        Set the attribute .sections to the passed dictionary
        """
        # Check
        assert sections

        # Assign to the surface the index of the corresponding section
        for key in sections:
            sections[key].surface.suid = key

        # `i` is the index of the rupture of the `n` admitted by this source.
        # In this loop we check that all the IDs of the sections composing one
        # rupture have a object in the sections dictionary describing their
        # geometry.
        self.sections = sections
        msg = 'Rupture #{:d}: section "{:s}" does not exist'
        for i in range(len(self.mags)):
            for idx in self.rupture_idxs[i]:
                if idx not in sections:
                    raise ValueError(msg.format(i, idx))

    def iter_ruptures(self, fromidx=0, untilidx=None, **kwargs):
        """
        An iterator for the ruptures.

        :param fromidx: start
        :param untilidx: stop
        """
        # Check
        if 'sections' not in self.__dict__:
            raise RuntimeError('You forgot to call set_sections in %s!' % self)

        # iter on the ruptures
        step = kwargs.get('step', 1)
        untilidx = len(self.mags) if untilidx is None else untilidx
        s = self.sections
        for i in range(fromidx, untilidx, step**2):
            idxs = self.rupture_idxs[i]
            if len(idxs) == 1:
                sfc = self.sections[idxs[0]].surface
            else:
                sfc = MultiSurface([s[idx].surface for idx in idxs])
            rake = self.rakes[i]
            hypo = self.sections[idxs[0]].surface.get_middle_point()
            yield NonParametricProbabilisticRupture(
                self.mags[i], rake, self.tectonic_region_type, hypo, sfc,
                self.pmfs[i])

    def __iter__(self):
        if len(self.mags) <= BLOCKSIZE:  # already split
            yield self
            return
        # split in blocks of BLOCKSIZE ruptures each
        for i, slc in enumerate(gen_slices(0, len(self.mags), BLOCKSIZE)):
            src = self.__class__(
                '%s:%d' % (self.source_id, i),
                self.name,
                self.tectonic_region_type,
                self.rupture_idxs[slc],
                self.pmfs[slc],
                self.mags[slc],
                self.rakes[slc])
            src.set_sections(self.sections)
            src.num_ruptures = src.count_ruptures()
            yield src

    def count_ruptures(self):
        """
        :returns: the number of the ruptures in the source
        """
        return len(self.mags)

    def get_min_max_mag(self):
        return np.min(self.mags), np.max(self.mags)

    def get_one_rupture(self, ses_seed, rupture_mutex):
        raise NotImplementedError

    @property
    def data(self):  # compatibility with NonParametricSeismicSource
        for i, rup in enumerate(self.iter_ruptures()):
            yield rup, self.pmfs[i]

    polygon = NP.polygon
    wkt = NP.wkt
    mesh_size = NP.mesh_size

    def get_bounding_box(self, maxdist):
        """
        Bounding box containing the surfaces, enlarged by the maximum distance
        """
        surfaces = []
        for sec in self.sections.values():
            if isinstance(sec.surface, MultiSurface):
                surfaces.extend(sec.surface.surfaces)
            else:
                surfaces.append(sec.surface)
        multi_surf = MultiSurface(surfaces)
        west, east, north, south = multi_surf.get_bounding_box()
        a1 = maxdist * KM_TO_DEGREES
        a2 = angular_distance(maxdist, north, south)
        return west - a2, south - a1, east + a2, north + a1
