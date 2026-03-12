from model.simulator import Simulation
from data.analyze import SimulationAnalyzer

config = {
    'video_bitrate': 4500, # kbps
    'fps': 60,
    'gop_size': 120,      # 2 секунды при 60 fps
    'audio_bitrate': 160,
    'bandwidth': 5000,    # kbps
    'network_delay': 0.05, # 50ms
    'jitter_intensity': 0.01,
    'packet_loss_probability': 0.005,
    'initial_buffer_duration': 2.0,
    'av_sync_threshold': 40, # ms
    'random_seed': 42
}

if __name__ == "__main__":
    analyzer = SimulationAnalyzer()
    for _ in range(500):
        print(f"Запуск симуляции {_+1}")
        sim = Simulation(config)
        sim.run(5000)
        analyzer.save_run(sim.stats)
    analyzer.analyze()      


