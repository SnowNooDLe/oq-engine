# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013-2021 GEM Foundation
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
Module exports :class:`DerrasEtAl2014`
"""
import numpy as np
from scipy.constants import g

from openquake.baselib.general import CallableDict
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable
from openquake.hazardlib import const
from openquake.hazardlib.imt import PGA, PGV, SA

# Constants used to normalise the input parameters
CONSTANTS = {
    "minMw": 3.6,
    "maxMw": 7.6,
    "logMinR": np.log10(0.1),
    "logMaxR": np.log10(547.0),
    "minD": 0.0,
    "maxD": 25.0,
    "logMinVs30": np.log10(92.0),
    "logMaxVs30": np.log10(1597.7),
    "minFM": 1.0,
    "maxFM": 4.0}


def rhypo_to_rjb(rhypo, mag):
    """
    Converts hypocentral distance to an equivalent Joyner-Boore distance
    dependent on the magnitude
    """
    epsilon = rhypo - (4.853 + 1.347E-6 * (mag ** 8.163))
    rjb = np.zeros_like(rhypo)
    idx = epsilon >= 3.
    rjb[idx] = np.sqrt((epsilon[idx] ** 2.) - 9.0)
    rjb[rjb < 0.0] = 0.0
    return rjb


def _get_normalised_term(pval, pmax, pmin):
    """
    Normalisation of a variable between its minimum and maximum using:
    2.0 * ((p - p_min) / (p_max - p_min)) - 1
    N.B. This is given as 0.5 * (...) - 1 in the paper, but the Electronic
    Supplement implements it as 2.0 * (...) - 1
    """
    return 2.0 * ((pval - pmin) / (pmax - pmin)) - 1


def _get_sof_dummy_variable(rake):
    """
    Authors use a style of faulting dummy variable of 1 for normal
    faulting, 2 for reverse faulting and 3 for strike-slip
    """
    if (rake > 45.0) and (rake < 135.0):
        # Reverse faulting
        return 3.0
    elif (rake < -45.0) and (rake > -135.0):
        # Normal faulting
        return 1.0
    else:
        # Strike slip
        return 4.0


get_pn = CallableDict()  # overridden in germany_2008


@get_pn.add("base")
def get_pn_base(region, rup, sites, dists, sof):
    """
    Normalise the input parameters within their upper and lower
    defined range
    """
    # List must be in following order
    p_n = []
    # Rjb
    # Note that Rjb must be clipped at 0.1 km
    rjb = np.copy(dists.rjb)
    rjb[rjb < 0.1] = 0.1
    p_n.append(_get_normalised_term(np.log10(rjb),
                                    CONSTANTS["logMaxR"],
                                    CONSTANTS["logMinR"]))
    # Magnitude
    p_n.append(_get_normalised_term(rup.mag,
                                    CONSTANTS["maxMw"],
                                    CONSTANTS["minMw"]))
    # Vs30
    p_n.append(_get_normalised_term(np.log10(sites.vs30),
                                    CONSTANTS["logMaxVs30"],
                                    CONSTANTS["logMinVs30"]))
    # Depth
    p_n.append(_get_normalised_term(rup.hypo_depth,
                                    CONSTANTS["maxD"],
                                    CONSTANTS["minD"]))
    # Style of Faulting
    p_n.append(_get_normalised_term(sof,
                                    CONSTANTS["maxFM"],
                                    CONSTANTS["minFM"]))
    return p_n


@get_pn.add("germany")
def get_pn_germany(region, rup, sites, dists, sof):
    """
    Normalise the input parameters within their upper and lower
    defined range
    """
    # List must be in following order
    p_n = []
    # Rjb
    # Note that Rjb must be clipped at 0.1 km
    if rup.width > 1.0E-3:
        rjb = np.copy(dists.rjb)
    else:
        rjb = rhypo_to_rjb(dists.rhypo, rup.mag)
    rjb[rjb < 0.1] = 0.1
    p_n.append(_get_normalised_term(np.log10(rjb),
                                    CONSTANTS["logMaxR"],
                                    CONSTANTS["logMinR"]))
    # Magnitude
    p_n.append(_get_normalised_term(rup.mag,
                                    CONSTANTS["maxMw"],
                                    CONSTANTS["minMw"]))
    # Vs30
    p_n.append(_get_normalised_term(np.log10(sites.vs30),
                                    CONSTANTS["logMaxVs30"],
                                    CONSTANTS["logMinVs30"]))
    # Depth
    p_n.append(_get_normalised_term(rup.hypo_depth,
                                    CONSTANTS["maxD"],
                                    CONSTANTS["minD"]))
    # Style of Faulting
    p_n.append(_get_normalised_term(sof,
                                    CONSTANTS["maxFM"],
                                    CONSTANTS["minFM"]))
    return p_n


def get_stddevs(C, n_sites, stddev_types):
    """
    Returns the standard deviations - originally given
    in terms of log_10, so converting to log_e
    """
    tau = C["tau"] + np.zeros(n_sites)
    phi = C["phi"] + np.zeros(n_sites)
    stddevs = []
    for stddev_type in stddev_types:
        if stddev_type == const.StdDev.TOTAL:
            sigma = np.log(10.0 ** (np.sqrt(tau ** 2. + phi ** 2.)))
            stddevs.append(sigma)
        elif stddev_type == const.StdDev.INTRA_EVENT:
            stddevs.append(np.log(10.0 ** phi))
        elif stddev_type == const.StdDev.INTER_EVENT:
            stddevs.append(np.log(10.0 ** tau))
    return stddevs


class DerrasEtAl2014(GMPE):
    """
    Implements GMPE developed by:
    B. Derras, P. Y. Bard, F. Cotton (2014) "Toward fully data driven ground-
    motion prediction models for Europe", Bulletin of Earthquake Engineering
    12, 495-516

    The GMPE is derived from an artifical neural network approach, and
    therefore does not assume the form of source, path and site scaling that is
    conventionally adopted by GMPEs. Instead the influence of each variable
    is modelled via a hyperbolic tangent-sigmoid function which is then applied
    to the vector of normalised predictor variables. As a consequence the
    expected ground motion for each site is derived from a set of matrix
    products from the respective weighting and bias vectors. This means that
    vectorisation by sites cannot be achieved and a loop is implemented
    instead.
    """
    region = "base"

    #: The supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: The supported intensity measure types are PGA, PGV, and SA
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = {PGA, PGV, SA}

    #: The supported intensity measure component is 'average horizontal',
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = const.IMC.AVERAGE_HORIZONTAL

    #: The supported standard deviations are total, inter and intra event
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL,
        const.StdDev.INTER_EVENT,
        const.StdDev.INTRA_EVENT
    ])

    #: The required site parameter is vs30
    REQUIRES_SITES_PARAMETERS = {'vs30'}

    #: The required rupture parameters are rake and magnitude
    REQUIRES_RUPTURE_PARAMETERS = {'rake', 'mag', 'hypo_depth'}

    #: The required distance parameter is 'Joyner-Boore' distance
    REQUIRES_DISTANCES = {'rjb'}

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        C = self.COEFFS[imt]
        # Get the mean
        mean = self.get_mean(C, rup, sites, dists)
        if imt.name == "PGV":
            # Convert from log10 m/s to ln cm/s
            mean = np.log((10.0 ** mean) * 100.)
        else:
            # convert from log10 m/s/s to ln g
            mean = np.log((10.0 ** mean) / g)

        # Get the standard deviations
        stddevs = get_stddevs(C, mean.shape, stddev_types)
        return mean, stddevs

    def get_mean(self, C, rup, sites, dists):
        """
        Returns the mean ground motion in terms of log10 m/s/s, implementing
        equation 2 (page 502)
        """
        # W2 needs to be a 1 by 5 matrix (not a vector
        w_2 = np.array([
            [C["W_21"], C["W_22"], C["W_23"], C["W_24"], C["W_25"]]
            ])
        # Gets the style of faulting dummy variable
        sof = _get_sof_dummy_variable(rup.rake)
        # Get the normalised coefficients
        p_n = get_pn(self.region,  rup, sites, dists, sof)
        mean = np.zeros_like(dists.rjb)
        # Need to loop over sites - maybe this can be improved in future?
        # ndenumerate is used to allow for application to 2-D arrays
        for idx, rval in np.ndenumerate(p_n[0]):
            # Place normalised coefficients into a single array
            p_n_i = np.array([rval, p_n[1], p_n[2][idx], p_n[3], p_n[4]])
            # Executes the main ANN model
            mean_i = np.dot(w_2, np.tanh(np.dot(self.W_1, p_n_i) + self.B_1))
            mean[idx] = (0.5 * (mean_i + C["B_2"] + 1.0) *
                         (C["tmax"] - C["tmin"])) + C["tmin"]
        return mean

    # Coefficients for the normalised output parameters and the standard
    # deviations. The former are taken from the Electronic Supplement to the
    # paper, whilst the latter are reported in Table 4
    COEFFS = CoeffsTable(sa_damping=5, table="""\
    imt                   tmin                 tmax                  W_21                W_22                 W_23                 W_24                  W_25                   B_2     tau     phi
    pgv    -3.8494850021680100  -0.0609239111303057   -0.5108267761681320   0.0705547785487647   0.2209141747955480   0.1688158389158400    0.1709281636238190  -0.0764727446960991   0.149   0.258
    pga    -2.9793036574208900   0.9810183503579470   -0.5410141503620630   0.2542513268001230   0.1097776172273200   0.0759590949968710   -0.0203475717695006  -0.1434930784597300   0.155   0.267
    0.010  -2.9851967249308700   0.9914516597246590   -0.5397735372214730   0.2543012574125800   0.1079740373017020   0.0748819979307182   -0.0215854294792677  -0.1412511667390830   0.155   0.268
    0.020  -2.9860592771710800   1.0077124420319700   -0.5393759310902680   0.2489420439884360   0.0994466712435390   0.0819871365119616   -0.0176628358022071  -0.1402921001720010   0.157   0.270
    0.030  -2.9841758145362700   1.0894952395988900   -0.5372084125784670   0.2404412781206790   0.0831456774341980   0.0874217720987058   -0.0180534593115691  -0.1424462376090170   0.160   0.276
    0.040  -2.9825522761997800   1.1566621151436100   -0.5206342580190630   0.2294225918588260   0.0640819890269353   0.0877235647991578   -0.0269902106014438  -0.1694035452552550   0.162   0.279
    0.050  -2.9566377219788700   1.1570953988072200   -0.5361435294571330   0.2379322017094610   0.0529587474813025   0.0798504289034170   -0.0405055241606587  -0.1686057780902590   0.163   0.281
    0.075  -2.9459804563422900   1.2607331074608400   -0.5546280636130240   0.2717556008480520   0.0503566319333317   0.0555940736542207   -0.0760453347003470  -0.1548592158007060   0.165   0.284
    0.100  -2.9363076345808300   1.4108142877985600   -0.5322665166770080   0.2914468968945670   0.0646170592452679   0.0552707941106321   -0.0964503498877211  -0.1690197091113510   0.168   0.290
    0.110  -2.9322166355719500   1.4577277923071400   -0.5215128792512610   0.2965867096510700   0.0695760247079559   0.0562737115252725   -0.0990624353396091  -0.1766136272223460   0.170   0.293
    0.120  -2.9305311375291000   1.4449914592215900   -0.5198772004016020   0.3011890551316260   0.0743266524551252   0.0548447531722862   -0.1029658495094730  -0.1704198073752260   0.170   0.292
    0.130  -2.9285425963598900   1.4530620363660300   -0.5148987743195460   0.3037547597744620   0.0817723836736415   0.0550681905859763   -0.1023106677399450  -0.1690129653555490   0.169   0.292
    0.140  -2.9196673126642800   1.3850373642004000   -0.5162158939482600   0.3134397947980450   0.0919389106853358   0.0523805390604297   -0.1023906820870020  -0.1639289532015240   0.170   0.293
    0.150  -2.9116971310363600   1.4717692347530400   -0.4979794995850170   0.3170187266665320   0.1021521946332690   0.0498359134240515   -0.0981672896924820  -0.1740083544141590   0.169   0.292
    0.160  -2.8705568997525400   1.4895420183953000   -0.4931767106638240   0.3270078628983330   0.1141829496237820   0.0492091819199796   -0.0948725836214985  -0.1944783861258280   0.168   0.290
    0.170  -2.8593355700991500   1.4908884937335900   -0.4857478781120660   0.3312535985763490   0.1272056140815920   0.0464184725116303   -0.0917363411984680  -0.2008014717185950   0.168   0.289
    0.180  -2.8730587645958800   1.4866172870411900   -0.4781912516799790   0.3353814666780460   0.1373250655602460   0.0442295221716087   -0.0884393991088352  -0.2031412936236190   0.167   0.288
    0.190  -2.8500590289332900   1.5037499302991000   -0.4725778368822180   0.3353557358116270   0.1441404667224620   0.0447290643462311   -0.0830593580179204  -0.2121347949463220   0.165   0.285
    0.200  -2.8346730052712600   1.5353949145918900   -0.4606756389203650   0.3316296218871790   0.1481014005941910   0.0513471795325157   -0.0744742378559087  -0.2147884447706200   0.164   0.284
    0.220  -2.7816474516543800   1.4090364464987300   -0.4554012863696480   0.3453620188396050   0.1684854523654020   0.0571549142765452   -0.0644918601474274  -0.2141824270627850   0.164   0.284
    0.240  -2.7587127627028800   1.2613190491473700   -0.4562901401401190   0.3599075311538000   0.1916373800357890   0.0581183907349576   -0.0551954667062526  -0.2139326390536270   0.164   0.282
    0.260  -2.7672142992978700   1.2328800873137700   -0.4489428577012490   0.3520377121866010   0.2060114119614530   0.0619618613915453   -0.0446763458089277  -0.2120082925765110   0.163   0.281
    0.280  -2.7539129775240000   1.2673005587893700   -0.4370333386072840   0.3405350070398710   0.2147075590644740   0.0647924028017897   -0.0312576308790298  -0.2270374840457480   0.161   0.279
    0.300  -2.6852493291163700   1.2694556822676200   -0.4499739611099390   0.3435506072145680   0.2320243598599740   0.0662676034963602   -0.0217727943584929  -0.2467388587050040   0.161   0.279
    0.320  -2.6991805763642700   1.2484271058697100   -0.4359142869138620   0.3278454583887470   0.2374133062955710   0.0688195968326906   -0.0112937781310018  -0.2479505796888810   0.163   0.282
    0.340  -2.6570613555195600   1.2616874302266000   -0.4246578404042180   0.3214088653882970   0.2477315961162920   0.0776129389334972    0.0023523038064737  -0.2518272001246020   0.164   0.284
    0.360  -2.7437796145718100   1.2454934926617400   -0.4156780409664940   0.3147539089045510   0.2559901586728200   0.0818650155768611    0.0151819981706302  -0.2128795651353130   0.165   0.285
    0.380  -2.7195497918478700   1.2125588720053700   -0.4153142558477670   0.3132625302105240   0.2667362278641250   0.0900050273237833    0.0273797732431594  -0.2155122777564500   0.166   0.286
    0.400  -2.6678719453367700   1.2067376317183300   -0.4148393323716700   0.3135090138545670   0.2763358576796840   0.1011428576097660    0.0395314004057325  -0.2328088293018920   0.165   0.285
    0.420  -2.6190431813951900   1.1839787015772600   -0.4180389717159100   0.3041648885898690   0.2794266748853570   0.1095410125090980    0.0555732927493092  -0.2426143478909290   0.165   0.284
    0.440  -2.6670814113367600   1.1882067311600000   -0.4122233327403940   0.2941850234308620   0.2801896101028070   0.1082438904742000    0.0657208292330138  -0.2307431723671490   0.164   0.283
    0.460  -2.7152952527243300   1.1875342933433100   -0.4057328308481130   0.2871560332561040   0.2831389560681230   0.1088576268241710    0.0745893379996742  -0.2196578428856080   0.164   0.283
    0.480  -2.7449377737603000   1.1950170564423600   -0.4042442949321190   0.2826540614689630   0.2896798342337830   0.1106937563488640    0.0820474670933300  -0.2103972308776420   0.164   0.284
    0.500  -2.7916168576169200   1.1628672472270300   -0.3983495545101600   0.2751342456016150   0.2934269446244130   0.1130998496578200    0.0914288908624079  -0.1977953081959260   0.164   0.283
    0.550  -2.9085176331735700   1.1492944969331100   -0.3829335031319720   0.2534509479512370   0.2975054555430770   0.1220898010344560    0.1158878365781790  -0.1605302161157090   0.165   0.285
    0.600  -2.9527892439411500   1.2262661309843900   -0.3733494878295400   0.2402565458756540   0.3033626561390710   0.1369612964952120    0.1390215245267430  -0.1408229861049840   0.166   0.286
    0.650  -3.0026215277061900   1.1741707545783800   -0.3737297590137460   0.2286575527083400   0.3127942905381040   0.1470137503552750    0.1606968958306870  -0.1078386841695510   0.166   0.287
    0.700  -3.0907155152427200   1.1282247021099500   -0.3595747879091110   0.2138390648396750   0.3131143596433960   0.1511687087496880    0.1780505303916640  -0.0940148618240067   0.166   0.287
    0.750  -3.1861000329639700   1.0529909418260700   -0.3457845093591480   0.1971871390764250   0.3112853868777880   0.1587308671541900    0.1930663079353090  -0.0738953365430371   0.167   0.287
    0.800  -3.2428377142230400   1.0356641472530100   -0.3410377613378580   0.1815362600786750   0.3150054375339770   0.1662013073727660    0.2064007448169790  -0.0579937199240750   0.166   0.287
    0.850  -3.3098183909070300   1.0066746524126100   -0.3362283844654920   0.1719300754280320   0.3206377441169860   0.1704889996865340    0.2148224986765460  -0.0422841140092537   0.165   0.285
    0.900  -3.3478678630973000   1.0223667326774400   -0.3310855303059200   0.1613174280558760   0.3224420373283380   0.1734924296476220    0.2223668830003590  -0.0436922077271728   0.166   0.286
    0.950  -3.3763632924771200   0.9939469522031180   -0.3286709399402540   0.1498864022427240   0.3233898520052460   0.1764115362533880    0.2290134059343970  -0.0279284754279632   0.167   0.288
    1.000  -3.4115407372712100   0.9665514895815880   -0.3230171734247490   0.1375672564720860   0.3230700604901910   0.1808357107147800    0.2309413468142540  -0.0054011463982554   0.168   0.290
    1.100  -3.4993495334897900   0.8871267401798590   -0.3180802493404970   0.1243289706983620   0.3317851615514970   0.1880067507057070    0.2388240852699050   0.0164308501469957   0.170   0.293
    1.200  -3.5986781202665600   0.7864526839073110   -0.3142209228842820   0.1158450868508410   0.3428200429190670   0.1962523122822420    0.2468832550954440   0.0564369809281568   0.172   0.297
    1.300  -3.6999711861320200   0.7733709022499610   -0.3105851723096060   0.1011155080198590   0.3454176627463390   0.2023311989700740    0.2517464908783650   0.0764154979483396   0.174   0.299
    1.400  -3.7879350245402200   0.7491360583715300   -0.3081864702345780   0.0840234064510466   0.3410894807211710   0.2007676727452840    0.2503944944640020   0.0800052849758061   0.177   0.305
    1.500  -3.8584851451030700   0.7801030153435410   -0.3066860473938940   0.0747038101272826   0.3420608999207350   0.2021422385782360    0.2455427938771910   0.0740356502837967   0.179   0.308
    1.600  -3.9197357230741200   0.7357733127234250   -0.3138768827368040   0.0710335065847289   0.3551929423792120   0.2044504163715720    0.2446083868540210   0.0929987701096936   0.180   0.310
    1.700  -3.9865291860204900   0.6429990500216410   -0.3146885420448420   0.0615551069292049   0.3561899834395030   0.2057362565875580    0.2427472311463730   0.0980909150382213   0.181   0.313
    1.800  -4.0370347010657600   0.6109513810330780   -0.3159626742658760   0.0498236128258896   0.3544717670256240   0.2017909436242210    0.2369306389801100   0.0949462342019402   0.183   0.316
    1.900  -4.0846735931012900   0.5982242299658990   -0.3139279332770400   0.0423509609886955   0.3537603183234680   0.1991631458487430    0.2339710370234500   0.0870020981022919   0.185   0.319
    2.000  -4.1236685284395200   0.5873171870931590   -0.3117335324254940   0.0380015978725541   0.3538673603704110   0.2001053693535210    0.2330666561399190   0.0806339322918566   0.184   0.319
    2.200  -4.2387778832468400   0.4948813686240000   -0.3206657494638550   0.0175043984865415   0.3550235841806770   0.2001083120780390    0.2327556274375540   0.0915109633943688   0.186   0.320
    2.400  -4.3439113217801100   0.4378318961619270   -0.3217988425844910   0.0031765916842267   0.3523017159503150   0.2048163038665100    0.2333086765062030   0.0949570801231493   0.186   0.320
    2.600  -4.4256986725969500   0.4195511027963140   -0.3222257216502840  -0.0046596561936244   0.3534079953257340   0.2073879114325200    0.2293888385211810   0.0952204306583157   0.187   0.323
    2.800  -4.4700290559690200   0.4277699005477710   -0.3220627029522440  -0.0158911129901433   0.3472459157261390   0.2090023880852250    0.2285790428580730   0.0865046630560831   0.188   0.324
    3.000  -4.5317431287605500   0.4550671374027660   -0.3237549464388110  -0.0228296340930483   0.3457464811150070   0.2086171933285430    0.2290736376985430   0.0809483142583118   0.189   0.326
    3.200  -4.6003297252732100   0.4662604822144270   -0.3260851512560800  -0.0251581680254629   0.3460812057425470   0.2060000808467140    0.2280369607329540   0.0696040680327187   0.190   0.327
    3.400  -4.6449413174440900   0.4756561952288580   -0.3263224567869750  -0.0280776334302466   0.3442566677875700   0.2027136653718320    0.2226307270185910   0.0597105130623805   0.190   0.327
    3.600  -4.6946699184550600   0.4736398903735540   -0.3287919421496010  -0.0330294887363268   0.3436469221704870   0.2000334235962920    0.2199215942475770   0.0511768464840134   0.189   0.326
    3.800  -4.7508447231052000   0.4676956353810650   -0.3309666276314150  -0.0382820403055363   0.3435683224798710   0.2014574493098730    0.2197797508897330   0.0536843640889908   0.188   0.325
    4.000  -4.7992997296092300   0.4447267414263530   -0.3319919140676440  -0.0418376481536162   0.3440063128328000   0.2035147583228230    0.2201758793657570   0.0561693756880409   0.188   0.324
    """)

    # Synaptic weights between input parameters and the hidden layer, as
    # taken from the Electronic Supplement
    W_1 = np.array([
        [2.6478916349996700, -1.0702179603728100,  0.1740877575500600,  0.0921912871948344, -0.0137636792052785],
        [-1.9086754364970900, -0.5350173685445370, -0.7051416226841650,  0.1676115828115410, -0.0266104896709684],
        [0.2035421429167090,  1.7805576356286200, -0.0804945913340041,  0.0135963560304775,  0.0615082092899090],
        [-0.6927374979706600,  0.4415052319560030,  0.7755799725513130, -0.0317177329335344, -0.1630657104941780],
        [0.0161628210842544,  0.2181413386066750, -1.6060994470735100, -0.0416362555063091,  0.0260579832482612]])

    # Bias vector of the hidden layer, as taken from the Electronic Supplement
    B_1 = np.array([-1.2712324878693900,
                    1.5126110282013300,
                    0.5910890088019860,
                    -0.1266226880549210,
                    -0.4157212218401920])


# Derras et al 2014
class DerrasEtAl2014RhypoGermany(DerrasEtAl2014):
    """
    Re-calibration of the Derras et al. (2014) GMPE taking hypocentral
    distance as an input and converting to Rjb
    """
    region = "germany"

    #: The required distance parameter is hypocentral distance
    REQUIRES_DISTANCES = {'rjb', 'rhypo'}
    REQUIRES_RUPTURE_PARAMETERS = {"rake", "mag", "hypo_depth", "width"}

    def __init__(self, adjustment_factor=1.0, **kwargs):
        super().__init__(adjustment_factor=adjustment_factor, **kwargs)
        self.adjustment_factor = np.log(adjustment_factor)

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """
        See :meth:`superclass method
        <.base.GroundShakingIntensityModel.get_mean_and_stddevs>`
        for spec of input and result values.
        """
        C = self.COEFFS[imt]
        # Get the mean
        mean = self.get_mean(C, rup, sites, dists)
        if imt.name == "PGV":
            # Convert from log10 m/s to ln cm/s
            mean = np.log((10.0 ** mean) * 100.)
        else:
            # convert from log10 m/s/s to ln g
            mean = np.log((10.0 ** mean) / g)

        # Get the standard deviations
        stddevs = get_stddevs(C, mean.shape, stddev_types)
        return mean + self.adjustment_factor, stddevs

    def get_mean(self, C, rup, sites, dists):
        """
        Returns the mean ground motion in terms of log10 m/s/s, implementing
        equation 2 (page 502)
        """
        # W2 needs to be a 1 by 5 matrix (not a vector
        w_2 = np.array([
            [C["W_21"], C["W_22"], C["W_23"], C["W_24"], C["W_25"]]])

        # Gets the style of faulting dummy variable
        sof = _get_sof_dummy_variable(rup.rake)

        # Get the normalised coefficients
        p_n = get_pn(self.region, rup, sites, dists, sof)

        mean = np.zeros_like(dists.rhypo)
        # Need to loop over sites - maybe this can be improved in future?
        # ndenumerate is used to allow for application to 2-D arrays
        for idx, rval in np.ndenumerate(p_n[0]):
            # Place normalised coefficients into a single array
            p_n_i = np.array([rval, p_n[1], p_n[2][idx], p_n[3], p_n[4]])
            # Executes the main ANN model
            mean_i = np.dot(w_2, np.tanh(np.dot(self.W_1, p_n_i) + self.B_1))
            mean[idx] = (0.5 * (mean_i + C["B_2"] + 1.0) *
                         (C["tmax"] - C["tmin"])) + C["tmin"]
        return mean
