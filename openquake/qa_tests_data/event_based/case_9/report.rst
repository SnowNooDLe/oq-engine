Event Based Risk SJ
===================

+----------------+----------------------+
| checksum32     | 82_891_453           |
+----------------+----------------------+
| date           | 2022-03-17T11:28:03  |
+----------------+----------------------+
| engine_version | 3.14.0-gitaed816bf7b |
+----------------+----------------------+
| input_size     | 12_421               |
+----------------+----------------------+

num_sites = 61, num_levels = 1, num_rlzs = 1

Parameters
----------
+---------------------------------+------------------------------------------+
| parameter                       | value                                    |
+---------------------------------+------------------------------------------+
| calculation_mode                | 'preclassical'                           |
+---------------------------------+------------------------------------------+
| number_of_logic_tree_samples    | 0                                        |
+---------------------------------+------------------------------------------+
| maximum_distance                | {'default': [[2.5, 50.0], [10.2, 50.0]]} |
+---------------------------------+------------------------------------------+
| investigation_time              | 25.0                                     |
+---------------------------------+------------------------------------------+
| ses_per_logic_tree_path         | 1                                        |
+---------------------------------+------------------------------------------+
| truncation_level                | 3.0                                      |
+---------------------------------+------------------------------------------+
| rupture_mesh_spacing            | 5.0                                      |
+---------------------------------+------------------------------------------+
| complex_fault_mesh_spacing      | 5.0                                      |
+---------------------------------+------------------------------------------+
| width_of_mfd_bin                | 0.3                                      |
+---------------------------------+------------------------------------------+
| area_source_discretization      | 20.0                                     |
+---------------------------------+------------------------------------------+
| pointsource_distance            | {'default': '1000'}                      |
+---------------------------------+------------------------------------------+
| ground_motion_correlation_model | 'JB2009'                                 |
+---------------------------------+------------------------------------------+
| minimum_intensity               | {}                                       |
+---------------------------------+------------------------------------------+
| random_seed                     | 23                                       |
+---------------------------------+------------------------------------------+
| master_seed                     | 123456789                                |
+---------------------------------+------------------------------------------+
| ses_seed                        | 42                                       |
+---------------------------------+------------------------------------------+

Input files
-----------
+-------------------------+----------------------------------------------------------------------+
| Name                    | File                                                                 |
+-------------------------+----------------------------------------------------------------------+
| gsim_logic_tree         | `Costa_Rica_RESIS_II_gmpe_CQ.xml <Costa_Rica_RESIS_II_gmpe_CQ.xml>`_ |
+-------------------------+----------------------------------------------------------------------+
| job_ini                 | `job.ini <job.ini>`_                                                 |
+-------------------------+----------------------------------------------------------------------+
| site_model              | `site_model_CR_60.xml <site_model_CR_60.xml>`_                       |
+-------------------------+----------------------------------------------------------------------+
| source_model_logic_tree | `sm_lt.xml <sm_lt.xml>`_                                             |
+-------------------------+----------------------------------------------------------------------+

Required parameters per tectonic region type
--------------------------------------------
+----------------------+-------------------+-----------+------------+---------------------+
| trt_smr              | gsims             | distances | siteparams | ruptparams          |
+----------------------+-------------------+-----------+------------+---------------------+
| Active Shallow Crust | [ZhaoEtAl2006Asc] | rrup      | vs30       | hypo_depth mag rake |
+----------------------+-------------------+-----------+------------+---------------------+

Slowest sources
---------------
+-----------+------+-----------+-----------+--------------+
| source_id | code | calc_time | num_sites | eff_ruptures |
+-----------+------+-----------+-----------+--------------+
| 1         | A    | 0.0       | 389       | 120          |
+-----------+------+-----------+-----------+--------------+

Computation times by source typology
------------------------------------
+------+-----------+-----------+--------------+--------+
| code | calc_time | num_sites | eff_ruptures | weight |
+------+-----------+-----------+--------------+--------+
| A    | 0.0       | 389       | 120          | 26.6   |
+------+-----------+-----------+--------------+--------+

Information about the tasks
---------------------------
+--------------------+--------+---------+--------+-----------+---------+---------+
| operation-duration | counts | mean    | stddev | min       | max     | slowfac |
+--------------------+--------+---------+--------+-----------+---------+---------+
| preclassical       | 2      | 0.01231 | 98%    | 2.146E-04 | 0.02441 | 1.98257 |
+--------------------+--------+---------+--------+-----------+---------+---------+
| read_source_model  | 1      | 0.00291 | nan    | 0.00291   | 0.00291 | 1.00000 |
+--------------------+--------+---------+--------+-----------+---------+---------+

Data transfer
-------------
+-------------------+---------------------------------------------+----------+
| task              | sent                                        | received |
+-------------------+---------------------------------------------+----------+
| read_source_model |                                             | 1.72 KB  |
+-------------------+---------------------------------------------+----------+
| split_task        | args=522.79 KB func=66 B elements=5 B       | 0 B      |
+-------------------+---------------------------------------------+----------+
| preclassical      | cmaker=519.34 KB sites=3.58 KB srcs=1.56 KB | 5.25 KB  |
+-------------------+---------------------------------------------+----------+

Slowest operations
------------------
+---------------------------+----------+-----------+--------+
| calc_50623, maxmem=2.0 GB | time_sec | memory_mb | counts |
+---------------------------+----------+-----------+--------+
| importing inputs          | 0.11022  | 0.0       | 1      |
+---------------------------+----------+-----------+--------+
| composite source model    | 0.09367  | 0.0       | 1      |
+---------------------------+----------+-----------+--------+
| total preclassical        | 0.02441  | 0.77344   | 1      |
+---------------------------+----------+-----------+--------+
| weighting sources         | 0.01878  | 0.0       | 20     |
+---------------------------+----------+-----------+--------+
| splitting sources         | 0.00482  | 0.0       | 1      |
+---------------------------+----------+-----------+--------+
| total read_source_model   | 0.00291  | 0.0       | 1      |
+---------------------------+----------+-----------+--------+