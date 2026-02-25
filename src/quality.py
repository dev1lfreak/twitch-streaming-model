"""Quality-of-Experience (QoE) metrics for the Twitch streaming model.

Aggregates per-step data from the buffer and encoder modules and produces
composite metrics that reflect the end-user's perceived quality:

* **A/V sync score** – how well audio and video remain synchronised.
* **Jerkiness score** – frequency and duration of playback stalls.
* **Quality stability score** – how frequently the quality level switches.
* **Overall QoE score** – weighted combination of the above (0–10 scale).
"""

from typing import List


class QualityMetrics:
    """Accumulates per-step simulation data and computes QoE scores.

    Parameters
    ----------
    av_sync_threshold_ms : float
        A/V drift above this value (ms) is perceived as out-of-sync
        (default 40.0 ms, roughly one video frame at 25 fps).
    jerk_weight : float
        Weight of the jerkiness component in the overall QoE (default 0.4).
    av_sync_weight : float
        Weight of the A/V sync component in the overall QoE (default 0.35).
    quality_stability_weight : float
        Weight of the quality stability component in the overall QoE
        (default 0.25).
    """

    def __init__(
        self,
        av_sync_threshold_ms: float = 40.0,
        jerk_weight: float = 0.4,
        av_sync_weight: float = 0.35,
        quality_stability_weight: float = 0.25,
    ) -> None:
        if abs(jerk_weight + av_sync_weight + quality_stability_weight - 1.0) > 1e-9:
            raise ValueError("QoE weights must sum to 1.0")
        self.av_sync_threshold_ms = av_sync_threshold_ms
        self.jerk_weight = jerk_weight
        self.av_sync_weight = av_sync_weight
        self.quality_stability_weight = quality_stability_weight

        self._steps: List[dict] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def record(self, buffer_state: dict, encoder_state: dict) -> None:
        """Record one simulation step.

        Parameters
        ----------
        buffer_state : dict
            Output of :meth:`src.buffer.StreamBuffer.step`.
        encoder_state : dict
            Output of :meth:`src.encoder.StreamEncoder.step`.
        """
        self._steps.append(
            {
                "is_stalled": buffer_state["is_stalled"],
                "stall_event": buffer_state["stall_event"],
                "buffer_level_s": buffer_state["level_s"],
                "av_sync_drift_ms": encoder_state["av_sync_drift_ms"],
                "quality_switch": encoder_state["quality_switch"],
                "quality_name": encoder_state["quality_name"],
                "dropped_frames": encoder_state["dropped_frames"],
            }
        )

    def compute(self) -> dict:
        """Compute aggregate QoE metrics over all recorded steps.

        Returns
        -------
        dict with keys:
            ``total_steps``          – number of steps recorded
            ``stall_count``          – number of stall events
            ``total_stall_time_s``   – total seconds spent stalled
            ``stall_ratio``          – fraction of time spent stalled
            ``mean_av_sync_drift_ms``– mean absolute A/V drift (ms)
            ``max_av_sync_drift_ms`` – maximum absolute A/V drift (ms)
            ``av_out_of_sync_ratio`` – fraction of steps with drift > threshold
            ``quality_switch_count`` – number of quality level changes
            ``quality_switch_rate``  – quality switches per minute
            ``mean_buffer_level_s``  – mean buffer level (seconds)
            ``dropped_frame_ratio``  – fraction of steps with dropped frames
            ``jerkiness_score``      – jerkiness component score (0–10)
            ``av_sync_score``        – A/V sync component score (0–10)
            ``quality_stability_score``– quality stability component (0–10)
            ``overall_qoe``          – overall QoE score (0–10)
        """
        n = len(self._steps)
        if n == 0:
            return {}

        stall_events = sum(1 for s in self._steps if s["stall_event"])
        stalled_steps = sum(1 for s in self._steps if s["is_stalled"])
        stall_ratio = stalled_steps / n

        abs_drifts = [abs(s["av_sync_drift_ms"]) for s in self._steps]
        mean_drift = sum(abs_drifts) / n
        max_drift = max(abs_drifts)
        out_of_sync_steps = sum(
            1 for d in abs_drifts if d > self.av_sync_threshold_ms
        )
        av_out_of_sync_ratio = out_of_sync_steps / n

        quality_switches = sum(1 for s in self._steps if s["quality_switch"])
        quality_switch_rate = quality_switches / n * 60  # per minute

        mean_buffer = sum(s["buffer_level_s"] for s in self._steps) / n

        dropped_steps = sum(1 for s in self._steps if s["dropped_frames"])
        dropped_frame_ratio = dropped_steps / n

        # ---- Component scores (0–10, higher = better) ----

        # Jerkiness: penalise stall ratio and dropped frames
        jerkiness_score = 10.0 * max(
            0.0, 1.0 - 3.0 * stall_ratio - dropped_frame_ratio
        )

        # A/V sync: penalise out-of-sync ratio and mean drift
        av_sync_score = 10.0 * max(
            0.0,
            1.0
            - av_out_of_sync_ratio
            - min(mean_drift / (10.0 * self.av_sync_threshold_ms), 1.0),
        )

        # Quality stability: penalise frequent switches
        # 1 switch/min is acceptable; more than 6/min is very bad
        quality_stability_score = 10.0 * max(
            0.0, 1.0 - quality_switch_rate / 6.0
        )

        overall_qoe = (
            self.jerk_weight * jerkiness_score
            + self.av_sync_weight * av_sync_score
            + self.quality_stability_weight * quality_stability_score
        )

        return {
            "total_steps": n,
            "stall_count": stall_events,
            "total_stall_time_s": stalled_steps,
            "stall_ratio": stall_ratio,
            "mean_av_sync_drift_ms": mean_drift,
            "max_av_sync_drift_ms": max_drift,
            "av_out_of_sync_ratio": av_out_of_sync_ratio,
            "quality_switch_count": quality_switches,
            "quality_switch_rate": quality_switch_rate,
            "mean_buffer_level_s": mean_buffer,
            "dropped_frame_ratio": dropped_frame_ratio,
            "jerkiness_score": jerkiness_score,
            "av_sync_score": av_sync_score,
            "quality_stability_score": quality_stability_score,
            "overall_qoe": overall_qoe,
        }

    def reset(self) -> None:
        """Clear all recorded data."""
        self._steps.clear()
