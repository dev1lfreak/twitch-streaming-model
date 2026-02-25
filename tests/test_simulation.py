"""Tests for src.simulation module."""

import pytest
from src.simulation import TwitchStreamSimulation


def test_run_returns_expected_keys():
    sim = TwitchStreamSimulation(duration_s=60, seed=0)
    report = sim.run()
    for key in (
        "total_steps",
        "stall_count",
        "stall_ratio",
        "mean_av_sync_drift_ms",
        "overall_qoe",
        "timeline",
    ):
        assert key in report


def test_timeline_length_matches_duration():
    sim = TwitchStreamSimulation(duration_s=60, dt=1.0, seed=0)
    report = sim.run()
    assert len(report["timeline"]) == 60


def test_overall_qoe_bounded():
    sim = TwitchStreamSimulation(duration_s=60, seed=1)
    report = sim.run()
    assert 0.0 <= report["overall_qoe"] <= 10.0


def test_stable_network_gives_better_qoe_than_poor():
    stable = TwitchStreamSimulation(
        duration_s=180,
        seed=42,
        network_kwargs={
            "base_bandwidth_mbps": 20.0,
            "oscillation_amplitude": 0.05,
            "congestion_probability": 0.001,
            "noise_sigma": 0.02,
        },
    )
    poor = TwitchStreamSimulation(
        duration_s=180,
        seed=42,
        network_kwargs={
            "base_bandwidth_mbps": 2.0,
            "oscillation_amplitude": 0.6,
            "congestion_probability": 0.15,
            "congestion_severity": 0.9,
            "noise_sigma": 0.3,
        },
    )
    stable_qoe = stable.run()["overall_qoe"]
    poor_qoe = poor.run()["overall_qoe"]
    assert stable_qoe > poor_qoe


def test_timeline_entries_have_required_fields():
    sim = TwitchStreamSimulation(duration_s=10, seed=0)
    report = sim.run()
    for entry in report["timeline"]:
        for field in (
            "t",
            "bandwidth_mbps",
            "buffer_level_s",
            "is_stalled",
            "quality_name",
            "av_sync_drift_ms",
        ):
            assert field in entry


def test_deterministic_with_same_seed():
    sim1 = TwitchStreamSimulation(duration_s=60, seed=7)
    sim2 = TwitchStreamSimulation(duration_s=60, seed=7)
    r1 = sim1.run()
    r2 = sim2.run()
    assert r1["overall_qoe"] == r2["overall_qoe"]
    assert r1["stall_count"] == r2["stall_count"]
