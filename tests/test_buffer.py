"""Tests for src.buffer module."""

import pytest
from src.buffer import StreamBuffer


def test_buffer_fills_with_high_inflow():
    buf = StreamBuffer(initial_level_s=0.0, rebuffer_threshold_s=0.0)
    state = buf.step(inflow_rate_s_per_s=5.0)
    assert state["level_s"] > 0.0
    assert not state["is_stalled"]


def test_buffer_drains_with_low_inflow():
    buf = StreamBuffer(initial_level_s=10.0)
    for _ in range(20):
        buf.step(inflow_rate_s_per_s=0.0)
    assert buf.level_s == 0.0


def test_stall_event_fires_when_buffer_empties():
    buf = StreamBuffer(initial_level_s=1.0, rebuffer_threshold_s=0.5, dt=1.0)
    stall_events = []
    for _ in range(5):
        state = buf.step(inflow_rate_s_per_s=0.0)
        stall_events.append(state["stall_event"])
    assert any(stall_events), "Expected at least one stall event"


def test_resume_event_fires_after_rebuffering():
    buf = StreamBuffer(
        initial_level_s=0.0,
        rebuffer_threshold_s=2.0,
        dt=1.0,
    )
    buf.is_stalled = True
    resume_events = []
    for _ in range(5):
        state = buf.step(inflow_rate_s_per_s=3.0)
        resume_events.append(state["resume_event"])
    assert any(resume_events), "Expected a resume event after refilling"


def test_buffer_capped_at_max_level():
    buf = StreamBuffer(max_level_s=10.0, initial_level_s=9.5, dt=1.0)
    state = buf.step(inflow_rate_s_per_s=10.0)
    assert state["level_s"] <= 10.0
    assert state["overflow"]


def test_invalid_rebuffer_threshold_raises():
    with pytest.raises(ValueError):
        StreamBuffer(max_level_s=5.0, rebuffer_threshold_s=10.0)


def test_stall_count_increments():
    buf = StreamBuffer(initial_level_s=1.0, rebuffer_threshold_s=0.0, dt=1.0)
    for _ in range(3):
        buf.step(inflow_rate_s_per_s=0.0)
    assert buf.stall_count >= 1


def test_reset_clears_stats():
    buf = StreamBuffer(initial_level_s=1.0, rebuffer_threshold_s=0.0, dt=1.0)
    for _ in range(5):
        buf.step(inflow_rate_s_per_s=0.0)
    buf.reset()
    assert buf.stall_count == 0
    assert buf.total_stall_time_s == 0.0
