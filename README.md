# twitch-streaming-model

An imitation model of the live-stream transmission process on the Twitch
platform, with a focus on **nonlinear system dynamics**: how the end-user's
perceived quality (audio/video synchronisation, playback jerkiness) depends on
network conditions and buffering settings.

---

## Model overview

The simulation is composed of four interacting modules that advance together
in discrete time steps (default: 1 second):

```
NetworkCondition ──► StreamEncoder ──► StreamBuffer
                                            │
                                      QualityMetrics  ──► QoE report
```

### `src/network.py` – NetworkCondition

Models time-varying network state with **nonlinear dynamics**:

| Variable | Model |
|---|---|
| Bandwidth B(t) | B_base · (1 + A·sin(2πft + φ)) · lognormal-noise · (1 − congestion) |
| Latency L(t) | L_base · (1 + 3·congestion²)  ← quadratic queuing effect |
| Packet loss P(t) | P_base + 0.1·congestion³  ← cubic nonlinearity |
| Congestion level | Sudden onset (random spike), gradual exponential recovery |

### `src/buffer.py` – StreamBuffer

Tracks the playback buffer level (seconds of pre-buffered content):

```
L(t+dt) = clamp( L(t) + (inflow − drain) · dt,  0, max )
```

* When `L == 0` → **stall event** (jerk perceived by viewer)
* After a stall, playback resumes only when `L ≥ rebuffer_threshold`
  (hysteresis, prevents rapid toggling)

### `src/encoder.py` – StreamEncoder

Adaptive-bitrate encoder with 7 quality levels (160p → 1080p60):

* **Immediate downgrade** when bandwidth falls below the current level's threshold
* **Hysteresis for upgrades** – requires N consecutive steps with spare bandwidth
* **A/V sync drift** accumulates during stalls and quality switches:

```
drift(t+1) = drift(t) · decay  +  noise  +  stall_penalty  +  switch_penalty
```

### `src/quality.py` – QualityMetrics

Computes three component scores (0–10, higher = better) and a weighted
overall QoE:

| Component | Weight | Penalises |
|---|---|---|
| Jerkiness score | 0.40 | stall ratio, dropped-frame ratio |
| A/V sync score | 0.35 | out-of-sync ratio, mean drift |
| Quality stability | 0.25 | quality-switch rate |

---

## Quick start

```bash
pip install -r requirements.txt
python main.py
```

Sample output:

```
====================================================
 Scenario: Stable network
----------------------------------------------------
 Twitch Stream Simulation – QoE Report
----------------------------------------------------
  Total steps (seconds)                300
  Stall events                         0
  ...
  Overall QoE         (0–10)           9.90
----------------------------------------------------
```

---

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

36 tests cover all four modules.

---

## Project structure

```
twitch-streaming-model/
├── main.py              # Demo: runs 3 network scenarios
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── network.py       # Nonlinear network condition model
│   ├── buffer.py        # Playback buffer with stall detection
│   ├── encoder.py       # Adaptive-bitrate encoder + A/V sync
│   ├── quality.py       # QoE metrics aggregation
│   └── simulation.py    # Discrete-time simulation orchestrator
└── tests/
    ├── test_network.py
    ├── test_buffer.py
    ├── test_encoder.py
    ├── test_quality.py
    └── test_simulation.py
```