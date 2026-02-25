"""Tests for src.encoder module."""

import pytest
from src.encoder import StreamEncoder, QUALITY_LADDER


def _dummy_buf(is_stalled: bool = False) -> dict:
    return {
        "is_stalled": is_stalled,
        "stall_event": False,
        "level_s": 5.0,
        "resume_event": False,
        "overflow": False,
    }


def test_encoder_selects_low_quality_on_low_bandwidth():
    enc = StreamEncoder(seed=0)
    state = enc.step(available_bandwidth_mbps=0.3, buffer_state=_dummy_buf())
    assert state["quality_name"] == QUALITY_LADDER[0].name


def test_encoder_selects_high_quality_on_high_bandwidth():
    enc = StreamEncoder(upgrade_hysteresis=1, seed=0)
    # Provide abundant bandwidth for several steps to overcome hysteresis
    for _ in range(5):
        state = enc.step(available_bandwidth_mbps=20.0, buffer_state=_dummy_buf())
    assert state["quality_name"] == QUALITY_LADDER[-1].name


def test_immediate_downgrade_on_bandwidth_drop():
    enc = StreamEncoder(upgrade_hysteresis=1, seed=0)
    # Ramp up quality
    for _ in range(5):
        enc.step(available_bandwidth_mbps=20.0, buffer_state=_dummy_buf())
    # Now drop bandwidth drastically
    state = enc.step(available_bandwidth_mbps=0.2, buffer_state=_dummy_buf())
    assert state["quality_name"] == QUALITY_LADDER[0].name


def test_av_sync_drift_increases_during_stall():
    enc = StreamEncoder(av_sync_noise=0.0, seed=0)
    # Normal step
    enc.step(available_bandwidth_mbps=5.0, buffer_state=_dummy_buf(is_stalled=False))
    drift_before = abs(enc.av_sync_drift_ms)
    # Stall step
    enc.step(available_bandwidth_mbps=5.0, buffer_state=_dummy_buf(is_stalled=True))
    drift_after = abs(enc.av_sync_drift_ms)
    assert drift_after > drift_before


def test_dropped_frames_during_stall():
    enc = StreamEncoder(seed=0)
    state = enc.step(
        available_bandwidth_mbps=5.0, buffer_state=_dummy_buf(is_stalled=True)
    )
    assert state["dropped_frames"]


def test_inflow_rate_positive():
    enc = StreamEncoder(seed=0)
    state = enc.step(available_bandwidth_mbps=5.0, buffer_state=_dummy_buf())
    assert state["inflow_rate_s_per_s"] > 0.0


def test_reset_clears_state():
    enc = StreamEncoder(upgrade_hysteresis=1, seed=0)
    for _ in range(5):
        enc.step(available_bandwidth_mbps=20.0, buffer_state=_dummy_buf())
    enc.reset()
    assert enc._quality_index == 0
    assert enc.av_sync_drift_ms == 0.0
