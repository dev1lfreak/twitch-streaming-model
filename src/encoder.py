"""Adaptive-bitrate encoder simulation for the Twitch streaming model.

The encoder selects a video quality level based on the available bandwidth
reported by the network module and the current buffer state.  It also tracks
audio/video synchronisation drift, which accumulates whenever frames are
dropped or the bitrate ladder switches unexpectedly.
"""

import math
from typing import List


# ---------------------------------------------------------------------------
# Quality level definitions (bandwidth thresholds in Mbit/s and bitrates)
# ---------------------------------------------------------------------------

QUALITY_LEVELS = [
    # (name,          video_kbps, audio_kbps, min_bandwidth_mbps)
    ("160p",          300,         96,         0.5),
    ("360p",          800,        128,         1.2),
    ("480p",         1500,        160,         2.5),
    ("720p",         3000,        192,         4.0),
    ("720p60",       4500,        192,         6.0),
    ("1080p",        6000,        320,         8.0),
    ("1080p60",      8000,        320,        10.0),
]


class QualityLevel:
    """Describes a single encoder quality level."""

    def __init__(self, name: str, video_kbps: int, audio_kbps: int, min_bandwidth_mbps: float) -> None:
        self.name = name
        self.video_kbps = video_kbps
        self.audio_kbps = audio_kbps
        self.min_bandwidth_mbps = min_bandwidth_mbps

    @property
    def total_kbps(self) -> int:
        return self.video_kbps + self.audio_kbps

    @property
    def total_mbps(self) -> float:
        return self.total_kbps / 1000.0

    def __repr__(self) -> str:
        return f"QualityLevel({self.name}, {self.total_kbps} kbps)"


# Build the sorted quality ladder (ascending bandwidth requirement)
QUALITY_LADDER: List[QualityLevel] = [
    QualityLevel(name, vkbps, akbps, mbw)
    for name, vkbps, akbps, mbw in QUALITY_LEVELS
]


class StreamEncoder:
    """Adaptive-bitrate encoder with A/V sync tracking.

    The encoder selects the highest quality level whose ``min_bandwidth_mbps``
    fits within ``safety_factor * available_bandwidth``.  A hysteresis
    mechanism prevents rapid quality oscillations (up-switch only after
    ``upgrade_hysteresis`` consecutive steps with sufficient bandwidth;
    down-switch is immediate).

    Audio/video synchronisation drift is accumulated according to::

        drift(t+1) = drift(t) * decay + delta(t)

    where ``delta`` is a random perturbation that grows with:
    * dropped frames (buffer stall)
    * large quality switches

    Parameters
    ----------
    safety_factor : float
        Fraction of available bandwidth the encoder may actually use
        (default 0.85, leaving headroom for overhead).
    upgrade_hysteresis : int
        Number of consecutive steps with spare bandwidth before upgrading
        quality (default 3).
    av_sync_decay : float
        Per-step exponential decay of A/V sync drift (0–1, default 0.95).
    av_sync_noise : float
        Base random A/V sync perturbation per step in milliseconds
        (default 0.5).
    seed : int or None
        Random seed.
    """

    def __init__(
        self,
        safety_factor: float = 0.85,
        upgrade_hysteresis: int = 3,
        av_sync_decay: float = 0.95,
        av_sync_noise: float = 0.5,
        seed: int = None,
    ) -> None:
        import numpy as np

        self.safety_factor = safety_factor
        self.upgrade_hysteresis = upgrade_hysteresis
        self.av_sync_decay = av_sync_decay
        self.av_sync_noise = av_sync_noise

        self._rng = np.random.default_rng(seed)
        self._quality_index = 0
        self._consecutive_upgrade_steps = 0
        self.av_sync_drift_ms: float = 0.0
        self.current_quality: QualityLevel = QUALITY_LADDER[0]

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def step(
        self,
        available_bandwidth_mbps: float,
        buffer_state: dict,
    ) -> dict:
        """Select quality and update A/V sync for this time step.

        Parameters
        ----------
        available_bandwidth_mbps : float
            Bandwidth available at this step.
        buffer_state : dict
            Output dict from :class:`~src.buffer.StreamBuffer.step`.

        Returns
        -------
        dict with keys:
            ``quality``          – current :class:`QualityLevel`
            ``quality_name``     – quality level name string
            ``inflow_rate_s_per_s`` – seconds of content delivered per second
            ``av_sync_drift_ms`` – A/V synchronisation drift in ms
            ``quality_switch``   – True if the quality level changed
            ``dropped_frames``   – True if frames were dropped this step
        """
        effective_bandwidth = available_bandwidth_mbps * self.safety_factor
        is_stalled = buffer_state.get("is_stalled", False)

        # ---- Quality selection ----
        target_index = self._select_quality_index(effective_bandwidth)
        previous_index = self._quality_index
        quality_switch = False

        if target_index < self._quality_index:
            # Immediate downgrade
            self._quality_index = target_index
            self._consecutive_upgrade_steps = 0
            quality_switch = True
        elif target_index > self._quality_index:
            self._consecutive_upgrade_steps += 1
            if self._consecutive_upgrade_steps >= self.upgrade_hysteresis:
                self._quality_index = target_index
                self._consecutive_upgrade_steps = 0
                quality_switch = True
        else:
            self._consecutive_upgrade_steps = 0

        self.current_quality = QUALITY_LADDER[self._quality_index]

        # ---- Inflow rate ----
        # Inflow is the content rate the encoder can deliver given available BW
        if is_stalled:
            # During stall we still receive data but don't drain
            inflow_rate = min(
                effective_bandwidth / self.current_quality.total_mbps,
                3.0,  # cap at 3× drain rate to avoid instant fill
            )
        else:
            inflow_rate = min(
                effective_bandwidth / self.current_quality.total_mbps,
                2.0,
            )

        # ---- Dropped frames ----
        # Frames are dropped when inflow < 1.0 (can't keep up with playback)
        dropped_frames = inflow_rate < 1.0 or is_stalled

        # ---- A/V sync drift ----
        base_noise = self._rng.normal(0.0, self.av_sync_noise)
        stall_penalty = 5.0 if is_stalled else 0.0
        switch_penalty = abs(self._quality_index - previous_index) * 2.0

        self.av_sync_drift_ms = (
            self.av_sync_drift_ms * self.av_sync_decay
            + base_noise
            + stall_penalty
            + switch_penalty
        )

        return {
            "quality": self.current_quality,
            "quality_name": self.current_quality.name,
            "inflow_rate_s_per_s": inflow_rate,
            "av_sync_drift_ms": self.av_sync_drift_ms,
            "quality_switch": quality_switch,
            "dropped_frames": dropped_frames,
        }

    def reset(self) -> None:
        """Reset the encoder to its initial state."""
        self._quality_index = 0
        self._consecutive_upgrade_steps = 0
        self.av_sync_drift_ms = 0.0
        self.current_quality = QUALITY_LADDER[0]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _select_quality_index(self, effective_bandwidth_mbps: float) -> int:
        """Return the index of the highest quality level that fits."""
        best = 0
        for i, level in enumerate(QUALITY_LADDER):
            if effective_bandwidth_mbps >= level.min_bandwidth_mbps:
                best = i
        return best
