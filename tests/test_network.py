"""Tests for src.network module."""

import pytest
from src.network import NetworkCondition


def test_step_returns_required_keys():
    net = NetworkCondition(seed=0)
    state = net.step()
    for key in ("bandwidth_mbps", "latency_ms", "packet_loss", "congestion_level"):
        assert key in state


def test_bandwidth_positive():
    net = NetworkCondition(seed=1)
    for _ in range(100):
        state = net.step()
        assert state["bandwidth_mbps"] > 0


def test_latency_increases_with_congestion():
    """Force full congestion and verify latency > base."""
    net = NetworkCondition(base_latency_ms=20.0, seed=2)
    net._congestion_level = 1.0
    state = net.step()
    assert state["latency_ms"] > 20.0


def test_packet_loss_bounded():
    net = NetworkCondition(seed=3)
    for _ in range(200):
        state = net.step()
        assert 0.0 <= state["packet_loss"] <= 1.0


def test_congestion_level_bounded():
    net = NetworkCondition(seed=4, congestion_probability=1.0)
    for _ in range(50):
        state = net.step()
        assert 0.0 <= state["congestion_level"] <= 1.0


def test_reset_restores_state():
    net = NetworkCondition(seed=5)
    for _ in range(30):
        net.step()
    net.reset(seed=5)
    assert net._step == 0
    assert net._congestion_level == 0.0


def test_deterministic_with_same_seed():
    net1 = NetworkCondition(seed=99)
    net2 = NetworkCondition(seed=99)
    for _ in range(20):
        s1 = net1.step()
        s2 = net2.step()
        assert abs(s1["bandwidth_mbps"] - s2["bandwidth_mbps"]) < 1e-9
