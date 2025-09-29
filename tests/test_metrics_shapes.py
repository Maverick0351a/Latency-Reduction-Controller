from lrc.metrics import MetricReader


def test_metric_reader_one_shot():
    mr = MetricReader()
    snap = mr.read(0.1)
    mr.close()
    assert set(snap.util.keys()) == {"CPU", "GPU", "RAM", "DISK", "NET"}
    assert 0.0 <= snap.util["CPU"] <= 1.0
