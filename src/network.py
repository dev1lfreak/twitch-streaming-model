"""Network condition simulation for the Twitch streaming model.

Models the nonlinear dynamics of network bandwidth, latency, and packet loss.
Bandwidth follows a base sinusoidal oscillation with multiplicative noise and
occasional congestion spikes, capturing realistic ISP traffic patterns.
"""

import numpy as np


class NetworkCondition:
    """Simulates time-varying network conditions.

    The bandwidth B(t) is modelled as a bounded nonlinear process::

        B(t) = B_base * (1 + A*sin(2π*f*t + φ)) * noise(t) * congestion(t)

    where:
    * ``B_base``      – mean available bandwidth (Mbit/s)
    * ``A``           – oscillation amplitude (0..1)
    * ``f``           – oscillation frequency (Hz)
    * ``noise(t)``    – log-normal multiplicative noise
    * ``congestion(t)``– occasional bandwidth drop (nonlinear spike model)

    Parameters
    ----------
    base_bandwidth_mbps : float
        Mean available bandwidth in Mbit/s (default 10.0).
    oscillation_amplitude : float
        Relative amplitude of sinusoidal variation (0–1, default 0.3).
    oscillation_freq_hz : float
        Frequency of the sinusoidal component in Hz (default 0.05).
    noise_sigma : float
        Std-dev of log-normal multiplicative noise (default 0.1).
    congestion_probability : float
        Per-step probability of a congestion event (default 0.02).
    congestion_severity : float
        Fraction of bandwidth lost during congestion (0–1, default 0.6).
    congestion_recovery_rate : float
        Rate at which congestion recovers per step (default 0.15).
    base_latency_ms : float
        Baseline one-way network latency in ms (default 20.0).
    base_packet_loss : float
        Baseline packet-loss probability (default 0.001).
    seed : int or None
        Random seed for reproducibility.
    """

    def __init__(
        self,
        base_bandwidth_mbps: float = 10.0,
        oscillation_amplitude: float = 0.3,
        oscillation_freq_hz: float = 0.05,
        noise_sigma: float = 0.1,
        congestion_probability: float = 0.02,
        congestion_severity: float = 0.6,
        congestion_recovery_rate: float = 0.15,
        base_latency_ms: float = 20.0,
        base_packet_loss: float = 0.001,
        seed: int = None,
    ) -> None:
        self.base_bandwidth_mbps = base_bandwidth_mbps
        self.oscillation_amplitude = oscillation_amplitude
        self.oscillation_freq_hz = oscillation_freq_hz
        self.noise_sigma = noise_sigma
        self.congestion_probability = congestion_probability
        self.congestion_severity = congestion_severity
        self.congestion_recovery_rate = congestion_recovery_rate
        self.base_latency_ms = base_latency_ms
        self.base_packet_loss = base_packet_loss

        self._rng = np.random.default_rng(seed)
        self._phase = self._rng.uniform(0, 2 * np.pi)
        self._congestion_level = 0.0  # 0 = none, 1 = full congestion

        self._step = 0
        self.dt = 1.0  # seconds per simulation step

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def step(self) -> dict:
        """Advance the network by one time step and return current state.

        Returns
        -------
        dict with keys:
            ``bandwidth_mbps``  – available bandwidth (Mbit/s)
            ``latency_ms``      – one-way latency (ms)
            ``packet_loss``     – packet-loss probability (0–1)
            ``congestion_level``– internal congestion level (0–1)
        """
        t = self._step * self.dt
        self._step += 1

        # Sinusoidal component (deterministic, nonlinear oscillation)
        sinusoidal = 1.0 + self.oscillation_amplitude * np.sin(
            2 * np.pi * self.oscillation_freq_hz * t + self._phase
        )

        # Multiplicative log-normal noise
        noise = self._rng.lognormal(mean=0.0, sigma=self.noise_sigma)

        # Congestion dynamics (nonlinear: onset is sudden, recovery is gradual)
        if self._rng.random() < self.congestion_probability:
            self._congestion_level = min(
                1.0, self._congestion_level + self.congestion_severity
            )
        else:
            self._congestion_level = max(
                0.0,
                self._congestion_level - self.congestion_recovery_rate,
            )

        availability = 1.0 - self._congestion_level

        bandwidth = max(
            0.1, self.base_bandwidth_mbps * sinusoidal * noise * availability
        )

        # Latency increases nonlinearly with congestion (queuing effect)
        latency = self.base_latency_ms * (
            1.0 + 3.0 * self._congestion_level ** 2
        )

        # Packet loss grows nonlinearly with congestion
        packet_loss = self.base_packet_loss + 0.1 * self._congestion_level ** 3

        return {
            "bandwidth_mbps": bandwidth,
            "latency_ms": latency,
            "packet_loss": packet_loss,
            "congestion_level": self._congestion_level,
        }

    def reset(self, seed: int = None) -> None:
        """Reset the network to its initial state."""
        if seed is not None:
            self._rng = np.random.default_rng(seed)
        self._phase = self._rng.uniform(0, 2 * np.pi)
        self._congestion_level = 0.0
        self._step = 0
