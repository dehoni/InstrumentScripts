"""This is the instrument implementation for the Zoom beamline."""
from logging import warning

from technique.sans.instrument import ScanningInstrument
from technique.sans.util import dae_setter
from general.scans.util import local_wrapper


class Zoom(ScanningInstrument):
    """This class handles the Zoom beamline, it is an extension
    of the Scanning instrument class."""
    def __init__(self):
        super().__init__()
        self._set_poslist_dls()

    def _generic_scan(self, detector, spectra, wiring="detector_1det_1dae3card.dat", tcbs=None):
        # Explicitly check and then set to default value to avoid UB.
        if tcbs is None:
            tcbs = [{"low": 5.0, "high": 100000.0, "step": 200.0, "trange": 1, "log": 0}]
        ScanningInstrument._generic_scan(self, detector, spectra, wiring, tcbs)

    @dae_setter("SANS", "sans")
    def setup_dae_event(self):
        print("Setting DAE into event mode")
        self._generic_scan(
            detector="detector_1det_1dae3card.dat",
            spectra="spec2det_280318_to_test_18_1.txt",
            wiring="wiring1det_event_200218.dat")

    @dae_setter("SANS", "sans")
    def setup_dae_histogram(self):
        self._generic_scan(
            detector="detector_1det_1dae3card.dat",
            spectra="spec2det_130218.txt",
            wiring="wiring1det_histogram_200218.dat")

    @dae_setter("TRANS", "transmission")
    def setup_dae_transmission(self):
        print("Setting up DAE for trans")
        self._generic_scan(
            detector="detector_8mon_1dae3card_00.dat",
            spectra="spectrum_8mon_1dae3card_00.dat",
            wiring="wiring_8mon_1dae3card_00_hist.dat")

    def set_aperture(self, size):
        warning("Setting the aperture is not implemented.")

    def _detector_is_on(self):
        """Is the detector currently on?"""
        voltage_status = all([
            self.get_pv(
                "CAEN:hv0:4:{}:status".format(x)).lower() == "on"
            for x in range(8)])
        return voltage_status

    def _detector_turn_on(self, delay=True):
        raise NotImplementedError("Detector toggling is not supported Zoom")

    def _detector_turn_off(self, delay=True):
        raise NotImplementedError("Detector toggling is not supported on Zoom")

    def _configure_sans_custom(self):
        # move the transmission monitor out
        self.send_pv("VACUUM:MONITOR:4:EXTRACT", "EXTRACT")

    def _configure_trans_custom(self):
        # move the transmission monitor in
        self.send_pv("VACUUM:MONITOR:4:INSERT", "INSERT")


obj = Zoom()
for method in obj.method_iterator():
    locals()[method] = local_wrapper(obj, method)
