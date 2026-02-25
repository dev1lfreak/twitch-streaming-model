"""Entry point for the Twitch live-stream imitation model.

Runs three illustrative scenarios and prints QoE reports:

1. **Stable network** – high bandwidth, low noise.
2. **Moderate network** – typical home broadband with some congestion.
3. **Poor network** – low bandwidth, frequent congestion events.
"""

from src.simulation import TwitchStreamSimulation


def run_scenario(name: str, network_kwargs: dict, seed: int = 42) -> None:
    print(f"\n{'='*52}")
    print(f" Scenario: {name}")
    sim = TwitchStreamSimulation(
        duration_s=300,
        seed=seed,
        network_kwargs=network_kwargs,
    )
    report = sim.run()
    TwitchStreamSimulation.print_report(report)


if __name__ == "__main__":
    run_scenario(
        "Stable network",
        network_kwargs={
            "base_bandwidth_mbps": 20.0,
            "oscillation_amplitude": 0.1,
            "congestion_probability": 0.005,
            "noise_sigma": 0.05,
        },
    )

    run_scenario(
        "Moderate network",
        network_kwargs={
            "base_bandwidth_mbps": 10.0,
            "oscillation_amplitude": 0.3,
            "congestion_probability": 0.02,
            "noise_sigma": 0.1,
        },
    )

    run_scenario(
        "Poor network",
        network_kwargs={
            "base_bandwidth_mbps": 3.0,
            "oscillation_amplitude": 0.5,
            "congestion_probability": 0.08,
            "congestion_severity": 0.8,
            "noise_sigma": 0.2,
        },
    )
