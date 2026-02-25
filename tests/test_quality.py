"""Tests for src.quality module."""

import pytest
from src.quality import QualityMetrics


def _buf(is_stalled: bool = False, stall_event: bool = False, level: float = 5.0):
    return {
        "is_stalled": is_stalled,
        "stall_event": stall_event,
        "level_s": level,
        "resume_event": False,
        "overflow": False,
    }


def _enc(drift: float = 0.0, switch: bool = False, dropped: bool = False, quality: str = "720p"):
    return {
        "av_sync_drift_ms": drift,
        "quality_switch": switch,
        "quality_name": quality,
        "dropped_frames": dropped,
    }


def test_compute_returns_empty_on_no_data():
    qm = QualityMetrics()
    assert qm.compute() == {}


def test_invalid_weights_raise():
    with pytest.raises(ValueError):
        QualityMetrics(jerk_weight=0.5, av_sync_weight=0.5, quality_stability_weight=0.5)


def test_perfect_stream_gives_high_qoe():
    qm = QualityMetrics()
    for _ in range(100):
        qm.record(_buf(), _enc(drift=0.0, dropped=False))
    result = qm.compute()
    assert result["overall_qoe"] >= 8.0
    assert result["stall_count"] == 0


def test_stall_reduces_qoe():
    qm = QualityMetrics()
    # Half the time stalled
    for _ in range(50):
        qm.record(_buf(is_stalled=True, stall_event=True), _enc(dropped=True))
    for _ in range(50):
        qm.record(_buf(), _enc())
    perfect_qm = QualityMetrics()
    for _ in range(100):
        perfect_qm.record(_buf(), _enc())
    assert qm.compute()["overall_qoe"] < perfect_qm.compute()["overall_qoe"]


def test_av_sync_drift_penalises_score():
    qm_good = QualityMetrics()
    qm_bad = QualityMetrics()
    for _ in range(100):
        qm_good.record(_buf(), _enc(drift=0.0))
        qm_bad.record(_buf(), _enc(drift=200.0))
    assert qm_bad.compute()["av_sync_score"] < qm_good.compute()["av_sync_score"]


def test_quality_switches_penalise_stability():
    qm_stable = QualityMetrics()
    qm_unstable = QualityMetrics()
    for _ in range(60):
        qm_stable.record(_buf(), _enc(switch=False))
        qm_unstable.record(_buf(), _enc(switch=True))
    assert (
        qm_unstable.compute()["quality_stability_score"]
        < qm_stable.compute()["quality_stability_score"]
    )


def test_stall_ratio_computation():
    qm = QualityMetrics()
    for _ in range(30):
        qm.record(_buf(is_stalled=True), _enc())
    for _ in range(70):
        qm.record(_buf(), _enc())
    result = qm.compute()
    assert abs(result["stall_ratio"] - 0.3) < 1e-9


def test_reset_clears_data():
    qm = QualityMetrics()
    for _ in range(10):
        qm.record(_buf(), _enc())
    qm.reset()
    assert qm.compute() == {}
