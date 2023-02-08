"""This is the instrument implementation for the Zoom beamline."""
from logging import warning

from technique.sans.instrument import ScanningInstrument
from technique.sans.util import dae_setter
from general.scans.util import local_wrapper
from .util import flipper1


class Zoom(ScanningInstrument):
    """This class handles the Zoom beamline, it is an extension
    of the Scanning instrument class."""
    def __init__(self):
        super().__init__()
        self._set_poslist_dls()

    def _generic_scan(self, detector, spectra, wiring="detector_1det_1dae3card.dat", tcbs=None):
        # Explicitly check and then set to default value to avoid UB.
        if tcbs is None:
            tcbs = [{"low": 5.0, "high": 100000.0, "step": 200.0, "trange": 1, "log": 0},
            {"low": 5.0, "high": 100000.0, "step": 200.0, "trange": 1,
                   "log": 0, "regime": 2}]
        ScanningInstrument._generic_scan(self, detector, spectra, wiring, tcbs)

    @property
    def TIMINGS(self):
        if self._dae_mode == "polsans":
            return self._TIMINGS + ["u", "d"]
        return self._TIMINGS        

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

    @dae_setter("SANS", "sans")
    def setup_dae_event_tshift(self):
        #second frame for 10-25 AA
        self._generic_scan(
            detector="detector_1det_1dae3card.dat",
            spectra="spec2det_280318_to_test_18_1.txt",
            wiring="wiring1det_event_200218.dat",
            tcbs=[{"low": 20000.0, "high": 120000.0, "step": 200.0, "trange": 1, "log": 0},
            {"low": 20000.0, "high": 120000.0, "step": 200.0, "trange": 1,
                   "log": 0, "regime": 2}])    

    @dae_setter("TRANS", "transmission")
    def setup_dae_transmission_tshift(self):
        #second frame for 10-25 AA
        print("Setting up DAE for trans")
        self._generic_scan(
            detector="detector_8mon_1dae3card_00.dat",
            spectra="spectrum_8mon_1dae3card_00.dat",
            wiring="wiring_8mon_1dae3card_00_hist.dat",
            tcbs=[{"low": 20000.0, "high": 120000.0, "step": 200.0, "trange": 1, "log": 0},
            {"low": 20000.0, "high": 120000.0, "step": 200.0, "trange": 1,
                   "log": 0, "regime": 2}])    

    @dae_setter("POLSANS", "polsans")
    def setup_dae_polsans(self):
        """Setup the instrument for POLSANS measurements."""
        self.setup_dae_event()

    @staticmethod
    def _begin_polsans():
        """Initialise a POLSANS run"""
        gen.change(nperiods=2)
        gen.begin(paused=1)

    @staticmethod
    def _waitfor_polsans(up_state_frames=600, down_state_frames=600, **kwargs):
        """Perform a POLSANS run"""
        if "uamps" in kwargs:
            get_total = gen.get_uamps
            key = "uamps"
        elif "seconds" in kwargs:
            get_total = gen.get_uamps
            key = "seconds"
        else:
            get_total = gen.get_frames
            key = "frames"
        gfrm = gen.get_frames()
        gtotal = get_total()

        if key == "seconds":
            gtotal=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
            up_state_frames=up_state_frames/10
            down_state_frames=down_state_frames/10

        while gtotal < kwargs[key]:
            gen.change(period=1)
            info("Flipper On")
            flipper1(1)
            if key == "seconds":
                gen.resume()
                ttime=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
                gen.waitfor(seconds=(gtotal+up_state_frames)-ttime)
                gen.pause()
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + up_state_frames)
                gen.pause()

            gen.change(period=2)
            info("Flipper Off")
            flipper1(0)
            if key == "seconds":
                gen.resume()
                ttime=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
                gen.waitfor(seconds=(gtotal+up_state_frames+down_state_frames)-ttime)
                gen.pause()
                gtotal=gen.get_pv("IN:ZOOM:DAE:RUNDURATION")
            else:
                gfrm = gen.get_frames()
                gen.resume()
                gen.waitfor(frames=gfrm + down_state_frames)
                gen.pause()
                gtotal = get_total()                        

    def set_aperture(self, size):
        warning("Setting the aperture is not implemented.")

    def _detector_is_on(self):
        """Is the detector currently on?"""
        return all(self.get_pv(f"CAEN:hv0:4:{x}:status").lower() == "on" for x in range(8))

    def _detector_turn_on(self, delay=True):
        raise NotImplementedError("Detector toggling is not supported Zoom")

    def _detector_turn_off(self, delay=True):
        raise NotImplementedError("Detector toggling is not supported on Zoom")

    def _configure_sans_custom(self):
        # move the transmission monitor out
        self.send_pv("VACUUM:MONITOR:2:EXTRACT","EXTRACT")
        self.send_pv("VACUUM:MONITOR:4:EXTRACT", "EXTRACT")

    def _configure_trans_custom(self):
        # move the transmission monitor in
        self.send_pv("VACUUM:MONITOR:2:EXTRACT","EXTRACT")
        self.send_pv("VACUUM:MONITOR:4:INSERT", "INSERT")


    def col_8m():
        print("8m configuration:choppers, colimator")
        gen.cset("PGC_Unit",101.45)
        gen.cset("disk2",97000)

    def guide_4m():    
        print("4m configuration:choppers, guide")
        gen.cset("PGC_Unit",0)
        gen.cset("disk2",99000)

    def polariser_4m():
        print("4m configuration:choppers, polariser")
        gen.cset("PGC_Unit",-125.5)
        gen.cset("disk2",99000)
        
        
    def polariser_8m():    
        print("8m configuration:choppers, polariser")
        gen.cset("PGC_Unit",-125.5)
        gen.cset("disk2",97000) 


obj = Zoom()
for method in obj.method_iterator():
    locals()[method] = local_wrapper(obj, method)
