from lrc.config import ControllerConfig
from lrc.controller import LRCController, ProcView


def test_hysteresis_signal():
    ctrl = LRCController(ControllerConfig())
    util_hot = {"CPU": 0.95, "GPU": 0.1, "RAM": 0.2, "DISK": 0.1, "NET": 0.1}
    util_calm = {"CPU": 0.10, "GPU": 0.1, "RAM": 0.2, "DISK": 0.1, "NET": 0.1}
    procs = [
        ProcView(1, "app.exe", True, 0.6, 0, 0),
        ProcView(2, "bg.exe", False, 0.4, 0, 0),
    ]
    decision_hot = ctrl.step(util_hot, procs)
    assert isinstance(decision_hot.acting, bool)
    decision_calm = ctrl.step(util_calm, procs)
    assert isinstance(decision_calm.telemetry["prci_sys"], float)
