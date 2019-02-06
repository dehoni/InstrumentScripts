"""Instrument is an example module of an instrument setup.

The motion commands simply adjust a global variable and the
measurement commands just print some information.  It should never be
used in production, but allows us to perform unit tests of the
remaining code without needing a full instrument for the testing
environment.

"""
from __future__ import print_function, division, unicode_literals

from general.scans.detector import BlockDetector
from general.scans.scans import ContinuousScan, ContinuousMove

from general.scans.defaults import Defaults
from general.scans.motion import BlockMotion, normalise_motion
from general.scans.util import local_wrapper


class LoqSampleChanger(Defaults):
    """
    This class represents the default functions for the Larmor instrument.
    """
    detector = BlockDetector("intensity")

    @staticmethod
    def log_file():
        from datetime import datetime
        now = datetime.now()
        return "loq_sample_changer_scan_{}_{}_{}_{}_{}_{}.dat".format(
            now.year, now.month, now.day, now.hour, now.minute, now.second)

    # FIXME We need a better way of handling the different defaults
    # pylint: disable=arguments-differ
    def scan(self, motion, centre=None, size=None, time=None, iterations=1):

        motion = normalise_motion(motion)

        if centre is None:
            raise TypeError("Scan centre must be provided")

        if size is None or size <= 0:
            raise TypeError("Move size not provided or invalid")

        if time is None or time <= 0:
            raise TypeError("Scan time not provided or invalid")

        time_single_direction = time / 2.0

        speed = size / time_single_direction

        start = centre + size/2.0
        stop = centre - size/2.0

        result = ContinuousScan(motion, [], self)

        for _ in range(iterations):
            result += ContinuousScan(motion,
                                     [ContinuousMove(start, stop, speed)],
                                     self).and_back

        return result

    def __repr__(self):
        return "{}()".format(self.__class__.__name__)


axis = BlockMotion("axis")

_loq_sample_changer = LoqSampleChanger()

scan = local_wrapper(_loq_sample_changer, "scan")
ascan = local_wrapper(_loq_sample_changer, "ascan")
dscan = local_wrapper(_loq_sample_changer, "dscan")
rscan = local_wrapper(_loq_sample_changer, "rscan")
