"""Stream buffer simulation for the Twitch streaming model.

Models the fill/drain dynamics of a playback buffer.  The buffer level is
measured in *seconds* of pre-buffered content.  An inflow rate (data arriving
from the network) is compared each step against a constant drain rate (the
playback speed).  When the buffer empties completely a *stall* (jerk) occurs.
"""


class StreamBuffer:
    """Playback buffer with fill/drain dynamics and stall detection.

    The buffer level L (in seconds of content) evolves each step as::

        L(t+dt) = clamp(L(t) + (inflow_rate - drain_rate) * dt, 0, max_level)

    A stall event is triggered whenever L(t) == 0 and playback is active.
    After a stall the buffer must refill to *rebuffer_threshold* seconds before
    playback resumes (hysteresis to avoid rapid toggle).

    Parameters
    ----------
    max_level_s : float
        Maximum buffer capacity in seconds of content (default 30.0).
    initial_level_s : float
        Starting buffer fill in seconds (default 5.0).
    rebuffer_threshold_s : float
        Minimum buffer level required to exit a stall (default 3.0).
    target_level_s : float
        Desired steady-state buffer level that the encoder targets (default 10.0).
    drain_rate_s_per_s : float
        Playback drain rate (always 1.0 second of content per second of wall
        time for normal 1× speed playback; default 1.0).
    dt : float
        Simulation step size in seconds (default 1.0).
    """

    def __init__(
        self,
        max_level_s: float = 30.0,
        initial_level_s: float = 5.0,
        rebuffer_threshold_s: float = 3.0,
        target_level_s: float = 10.0,
        drain_rate_s_per_s: float = 1.0,
        dt: float = 1.0,
    ) -> None:
        if rebuffer_threshold_s > max_level_s:
            raise ValueError(
                "rebuffer_threshold_s must be <= max_level_s"
            )
        self.max_level_s = max_level_s
        self.rebuffer_threshold_s = rebuffer_threshold_s
        self.target_level_s = target_level_s
        self.drain_rate_s_per_s = drain_rate_s_per_s
        self.dt = dt

        self.level_s: float = initial_level_s
        self.is_stalled: bool = False
        self.total_stall_time_s: float = 0.0
        self.stall_count: int = 0
        self._stall_started: bool = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def step(self, inflow_rate_s_per_s: float) -> dict:
        """Advance the buffer by one time step.

        Parameters
        ----------
        inflow_rate_s_per_s : float
            Seconds of content arriving per second of wall time (computed by
            the encoder from the current available bandwidth).

        Returns
        -------
        dict with keys:
            ``level_s``          – buffer level after the step (seconds)
            ``is_stalled``       – whether playback is currently stalled
            ``stall_event``      – True if a *new* stall began this step
            ``resume_event``     – True if playback resumed this step
            ``overflow``         – True if buffer hit its maximum this step
        """
        stall_event = False
        resume_event = False
        overflow = False

        if self.is_stalled:
            # While stalled only inflow occurs (drain is paused)
            self.level_s = min(
                self.max_level_s,
                self.level_s + inflow_rate_s_per_s * self.dt,
            )
            self.total_stall_time_s += self.dt

            if self.level_s >= self.rebuffer_threshold_s:
                self.is_stalled = False
                resume_event = True
        else:
            # Normal playback: drain at 1× speed
            net_rate = inflow_rate_s_per_s - self.drain_rate_s_per_s
            new_level = self.level_s + net_rate * self.dt

            if new_level >= self.max_level_s:
                self.level_s = self.max_level_s
                overflow = True
            elif new_level <= 0.0:
                self.level_s = 0.0
                self.is_stalled = True
                stall_event = True
                self.stall_count += 1
                self.total_stall_time_s += self.dt
            else:
                self.level_s = new_level

        return {
            "level_s": self.level_s,
            "is_stalled": self.is_stalled,
            "stall_event": stall_event,
            "resume_event": resume_event,
            "overflow": overflow,
        }

    def reset(self, initial_level_s: float = None) -> None:
        """Reset the buffer to its initial state."""
        if initial_level_s is None:
            initial_level_s = self.rebuffer_threshold_s
        self.level_s = initial_level_s
        self.is_stalled = False
        self.total_stall_time_s = 0.0
        self.stall_count = 0
        self._stall_started = False
