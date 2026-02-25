"""Main simulation orchestrator for the Twitch streaming model.

Ties together :class:`~src.network.NetworkCondition`,
:class:`~src.buffer.StreamBuffer`,
:class:`~src.encoder.StreamEncoder`, and
:class:`~src.quality.QualityMetrics` into a single discrete-time simulation.

Example usage::

    from src.simulation import TwitchStreamSimulation

    sim = TwitchStreamSimulation(duration_s=300, seed=42)
    result = sim.run()
    sim.print_report(result)
"""

from __future__ import annotations

from typing import List

from src.network import NetworkCondition
from src.buffer import StreamBuffer
from src.encoder import StreamEncoder
from src.quality import QualityMetrics


class TwitchStreamSimulation:
    """Discrete-time imitation model of Twitch live-stream delivery.

    Parameters
    ----------
    duration_s : int
        Simulation duration in seconds (default 300).
    dt : float
        Time step in seconds (default 1.0).
    network_kwargs : dict or None
        Keyword arguments forwarded to :class:`~src.network.NetworkCondition`.
    buffer_kwargs : dict or None
        Keyword arguments forwarded to :class:`~src.buffer.StreamBuffer`.
    encoder_kwargs : dict or None
        Keyword arguments forwarded to :class:`~src.encoder.StreamEncoder`.
    quality_kwargs : dict or None
        Keyword arguments forwarded to :class:`~src.quality.QualityMetrics`.
    seed : int or None
        Master random seed (propagated to sub-components unless overridden in
        their own kwargs).
    """

    def __init__(
        self,
        duration_s: int = 300,
        dt: float = 1.0,
        network_kwargs: dict = None,
        buffer_kwargs: dict = None,
        encoder_kwargs: dict = None,
        quality_kwargs: dict = None,
        seed: int = None,
    ) -> None:
        self.duration_s = duration_s
        self.dt = dt

        nkw = network_kwargs or {}
        bkw = buffer_kwargs or {}
        ekw = encoder_kwargs or {}
        qkw = quality_kwargs or {}

        if "seed" not in nkw:
            nkw["seed"] = seed
        if "seed" not in ekw:
            ekw["seed"] = seed

        self.network = NetworkCondition(**nkw)
        self.buffer = StreamBuffer(dt=dt, **bkw)
        self.encoder = StreamEncoder(**ekw)
        self.metrics = QualityMetrics(**qkw)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self) -> dict:
        """Run the full simulation and return the aggregated QoE report.

        Returns
        -------
        dict
            QoE metrics as returned by :meth:`~src.quality.QualityMetrics.compute`,
            plus ``timeline`` – a list of per-step state dicts.
        """
        self.network.reset()
        self.buffer.reset()
        self.encoder.reset()
        self.metrics.reset()

        timeline: List[dict] = []

        for step in range(int(self.duration_s / self.dt)):
            # 1. Observe network
            net = self.network.step()

            # 2. Encoder selects quality and computes inflow
            #    (needs current buffer state flags, use previous buffer state
            #    to avoid circular dependency)
            prev_buffer_state = {
                "is_stalled": self.buffer.is_stalled,
                "stall_event": False,
                "level_s": self.buffer.level_s,
                "resume_event": False,
                "overflow": False,
            }
            enc = self.encoder.step(net["bandwidth_mbps"], prev_buffer_state)

            # 3. Advance buffer with the inflow rate produced by the encoder
            buf = self.buffer.step(enc["inflow_rate_s_per_s"])

            # 4. Record QoE metrics
            self.metrics.record(buf, enc)

            # 5. Store timeline snapshot
            timeline.append(
                {
                    "t": step * self.dt,
                    "bandwidth_mbps": net["bandwidth_mbps"],
                    "latency_ms": net["latency_ms"],
                    "packet_loss": net["packet_loss"],
                    "congestion_level": net["congestion_level"],
                    "buffer_level_s": buf["level_s"],
                    "is_stalled": buf["is_stalled"],
                    "stall_event": buf["stall_event"],
                    "quality_name": enc["quality_name"],
                    "av_sync_drift_ms": enc["av_sync_drift_ms"],
                    "inflow_rate_s_per_s": enc["inflow_rate_s_per_s"],
                    "dropped_frames": enc["dropped_frames"],
                }
            )

        report = self.metrics.compute()
        report["timeline"] = timeline
        return report

    # ------------------------------------------------------------------
    # Reporting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def print_report(report: dict) -> None:
        """Print a human-readable summary of a simulation report.

        Parameters
        ----------
        report : dict
            Output of :meth:`run`.
        """
        sep = "-" * 52
        print(sep)
        print(" Twitch Stream Simulation – QoE Report")
        print(sep)
        keys_fmt = [
            ("total_steps",              "Total steps (seconds)",         "{:.0f}"),
            ("stall_count",              "Stall events",                  "{:.0f}"),
            ("total_stall_time_s",       "Total stall time (s)",          "{:.1f}"),
            ("stall_ratio",              "Stall ratio",                   "{:.3f}"),
            ("mean_av_sync_drift_ms",    "Mean A/V sync drift (ms)",      "{:.2f}"),
            ("max_av_sync_drift_ms",     "Max A/V sync drift (ms)",       "{:.2f}"),
            ("av_out_of_sync_ratio",     "A/V out-of-sync ratio",         "{:.3f}"),
            ("quality_switch_count",     "Quality switches",              "{:.0f}"),
            ("quality_switch_rate",      "Quality switch rate (/min)",    "{:.2f}"),
            ("mean_buffer_level_s",      "Mean buffer level (s)",         "{:.2f}"),
            ("dropped_frame_ratio",      "Dropped-frame ratio",           "{:.3f}"),
            ("jerkiness_score",          "Jerkiness score     (0–10)",    "{:.2f}"),
            ("av_sync_score",            "A/V sync score      (0–10)",    "{:.2f}"),
            ("quality_stability_score",  "Quality stability   (0–10)",    "{:.2f}"),
            ("overall_qoe",              "Overall QoE         (0–10)",    "{:.2f}"),
        ]
        for key, label, fmt in keys_fmt:
            if key in report:
                value_str = fmt.format(report[key])
                print(f"  {label:<36} {value_str}")
        print(sep)
