#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2013, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

"""
Helpers to import test data with the PGImporter
"""

from openquake.engine.tools.pg_importer import PGImporter

# id owner_id oq_job_id display_name output_type last_update
output = '''\
$out1	1	\N	gmf-rlz	gmf	2013-04-11 03:08:46.797773
'''

# id output_id lt_realization_id
gmf_collection = '''\
$coll1	$out1	\N
'''

# id gmf_collection_id investigation_time ses_ordinal
gmf_set = '''\
$set1	$coll1	10	1
$set2	$coll1	10	2
$set3	$coll1	10	3
'''

# id gmf_set_id imt sa_period sa_damping gmvs rupture_ids result_grp_ordinal location
gmf = '''\
$gmf01	$set1	SA	0.1	5	{0.729799582246203}	{709346}	1	0101000020E610000000000000000000000000000000000000
$gmf02	$set1	SA	0.1	5	{0.0141248596268433}	{709346}	1	0101000020E61000000000000000000000000000000000E03F
$gmf03	$set1	PGA	\N	\N	{0.252294938306868}	{709346}	1	0101000020E610000000000000000000000000000000000000
$gmf04	$set1	PGA	\N	\N	{0.00894558476907965}	{709346}	1	0101000020E61000000000000000000000000000000000E03F
$gmf05	$set3	SA	0.1	5	{0.73468651581123}	{709348}	1	0101000020E610000000000000000000000000000000000000
$gmf06	$set3	SA	0.1	5	{0.130897324686063}	{709348}	1	0101000020E61000000000000000000000000000000000E03F
$gmf07	$set3	PGA	\N	\N	{0.23164352054727}	{709348}	1	0101000020E610000000000000000000000000000000000000
$gmf08	$set3	PGA	\N	\N	{0.0264362061113464}	{709348}	1	0101000020E61000000000000000000000000000000000E03F
$gmf09	$set1	SA	0.1	5	{0.0571210320882165,0.0851203442596857,0.0512935367105168}	{709350,709352,709354}	2	0101000020E610000000000000000000000000000000000000
$gmf10	$set1	SA	0.1	5	{0.0457237221727419,0.0250737105548348,0.0466984811965513}	{709350,709352,709354}	2	0101000020E61000000000000000000000000000000000E03F
$gmf11	$set1	PGA	\N	\N	{0.151132933300216,0.0477298423601717,0.0142826375129993}	{709350,709352,709354}	2	0101000020E610000000000000000000000000000000000000
$gmf12	$set1	PGA	\N	\N	{0.0720017584564812,0.0209473778737383,0.00810452525440645}	{709350,709352,709354}	2	0101000020E61000000000000000000000000000000000E03F
$gmf13	$set1	SA	0.1	5	{0.0647094509155515}	{709356}	3	0101000020E610000000000000000000000000000000000000
$gmf14	$set1	SA	0.1	5	{0.0137011674890562}	{709356}	3	0101000020E61000000000000000000000000000000000E03F
$gmf15	$set1	PGA	\N	\N	{0.053177248284009}	{709356}	3	0101000020E610000000000000000000000000000000000000
$gmf16	$set1	PGA	\N	\N	{0.014933592444171}	{709356}	3	0101000020E61000000000000000000000000000000000E03F
$gmf17	$set1	SA	0.1	5	{0.156892787041029}	{709358}	4	0101000020E610000000000000000000000000000000000000
$gmf18	$set1	SA	0.1	5	{0.015367505662649}	{709358}	4	0101000020E61000000000000000000000000000000000E03F
$gmf19	$set1	PGA	\N	\N	{0.0346846321726566}	{709358}	4	0101000020E610000000000000000000000000000000000000
$gmf20	$set1	PGA	\N	\N	{0.0247923869973088}	{709358}	4	0101000020E61000000000000000000000000000000000E03F
$gmf21	$set2	SA	0.1	5	{0.0168322906204596}	{709360}	4	0101000020E610000000000000000000000000000000000000
$gmf22	$set2	SA	0.1	5	{0.0267122052505091}	{709360}	4	0101000020E61000000000000000000000000000000000E03F
$gmf23	$set2	PGA	\N	\N	{0.00509134495333861}	{709360}	4	0101000020E610000000000000000000000000000000000000
$gmf24	$set2	PGA	\N	\N	{0.0187720473080453}	{709360}	4	0101000020E61000000000000000000000000000000000E03F
$gmf25	$set3	SA	0.1	5	{0.0174152488960141}	{709362}	4	0101000020E610000000000000000000000000000000000000
$gmf26	$set3	SA	0.1	5	{0.00365106296335889}	{709362}	4	0101000020E61000000000000000000000000000000000E03F
$gmf27	$set3	PGA	\N	\N	{0.00327192823764393}	{709362}	4	0101000020E610000000000000000000000000000000000000
$gmf28	$set3	PGA	\N	\N	{0.00257996694936015}	{709362}	4	0101000020E61000000000000000000000000000000000E03F
'''

imts = [('PGA', None, None), ('SA', 0.1, 5)]

num_tasks = 4

# expected stochastic event set 1
set1_exp = '''\
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=709346
<X=  0.00000, Y=  0.00000, GMV=0.2522949>
<X=  0.00000, Y=  0.50000, GMV=0.0089456>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=709350
<X=  0.00000, Y=  0.00000, GMV=0.1511329>
<X=  0.00000, Y=  0.50000, GMV=0.0720018>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=709352
<X=  0.00000, Y=  0.00000, GMV=0.0477298>
<X=  0.00000, Y=  0.50000, GMV=0.0209474>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=709354
<X=  0.00000, Y=  0.00000, GMV=0.0142826>
<X=  0.00000, Y=  0.50000, GMV=0.0081045>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=709356
<X=  0.00000, Y=  0.00000, GMV=0.0531772>
<X=  0.00000, Y=  0.50000, GMV=0.0149336>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=709358
<X=  0.00000, Y=  0.00000, GMV=0.0346846>
<X=  0.00000, Y=  0.50000, GMV=0.0247924>)
GMF(imt=SA sa_period=0.1 sa_damping=5.0 rupture_id=709346
<X=  0.00000, Y=  0.00000, GMV=0.7297996>
<X=  0.00000, Y=  0.50000, GMV=0.0141249>)
GMF(imt=SA sa_period=0.1 sa_damping=5.0 rupture_id=709350
<X=  0.00000, Y=  0.00000, GMV=0.0571210>
<X=  0.00000, Y=  0.50000, GMV=0.0457237>)
GMF(imt=SA sa_period=0.1 sa_damping=5.0 rupture_id=709352
<X=  0.00000, Y=  0.00000, GMV=0.0851203>
<X=  0.00000, Y=  0.50000, GMV=0.0250737>)
GMF(imt=SA sa_period=0.1 sa_damping=5.0 rupture_id=709354
<X=  0.00000, Y=  0.00000, GMV=0.0512935>
<X=  0.00000, Y=  0.50000, GMV=0.0466985>)
GMF(imt=SA sa_period=0.1 sa_damping=5.0 rupture_id=709356
<X=  0.00000, Y=  0.00000, GMV=0.0647095>
<X=  0.00000, Y=  0.50000, GMV=0.0137012>)
GMF(imt=SA sa_period=0.1 sa_damping=5.0 rupture_id=709358
<X=  0.00000, Y=  0.00000, GMV=0.1568928>
<X=  0.00000, Y=  0.50000, GMV=0.0153675>)'''


# expected stochastic event set 2
set2_exp = '''\
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=709360
<X=  0.00000, Y=  0.00000, GMV=0.0050913>
<X=  0.00000, Y=  0.50000, GMV=0.0187720>)
GMF(imt=SA sa_period=0.1 sa_damping=5.0 rupture_id=709360
<X=  0.00000, Y=  0.00000, GMV=0.0168323>
<X=  0.00000, Y=  0.50000, GMV=0.0267122>)'''

# expected stochastic event set 3
set3_exp = '''\
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=709348
<X=  0.00000, Y=  0.00000, GMV=0.2316435>
<X=  0.00000, Y=  0.50000, GMV=0.0264362>)
GMF(imt=PGA sa_period=None sa_damping=None rupture_id=709362
<X=  0.00000, Y=  0.00000, GMV=0.0032719>
<X=  0.00000, Y=  0.50000, GMV=0.0025800>)
GMF(imt=SA sa_period=0.1 sa_damping=5.0 rupture_id=709348
<X=  0.00000, Y=  0.00000, GMV=0.7346865>
<X=  0.00000, Y=  0.50000, GMV=0.1308973>)
GMF(imt=SA sa_period=0.1 sa_damping=5.0 rupture_id=709362
<X=  0.00000, Y=  0.00000, GMV=0.0174152>
<X=  0.00000, Y=  0.50000, GMV=0.0036511>)'''


def import_a_gmf_collection(conn):
    """
    Import a fixed gmf_collection into the database. This is a useful
    helper to populate the risk tests without having to run a full hazard
    computation.

    :param conn: a DB API 2 connection

    conn.cursor() must return a psycopg2 cursor with a .copy_expert() method
    """
    PGImporter(conn).import_all([
        ('uiapi.output', output),
        ('hzrdr.gmf_collection', gmf_collection),
        ('hzrdr.gmf_set', gmf_set),
        ('hzrdr.gmf', gmf),
    ])
