from datetime import datetime
import json

from model.simulator import Simulation
from stats.analyze import SimulationAnalyzer
from stats.data_exporter import DataExporter

"""
    Стандартные параметры симуляции
"""
test_config = {
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

def load_simulation_config(file_path):
    """
    Загружает параметры симуляции из JSON файла.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Ошибка: Файл {file_path} не найден.")
        return None
    except json.JSONDecodeError:
        print(f"Ошибка: Некорректный формат JSON в файле {file_path}.")
        return None

if __name__ == "__main__":
    analyzer = SimulationAnalyzer()
    exporter = DataExporter()
    date = datetime.now()

    config = load_simulation_config('configs/standart_conf.json')
    for _ in range(500):
        print(f"Запуск симуляции {_+1}")
        sim = Simulation(config)
        sim.run(4000)
        analyzer.save_run(sim.stats)

    analyzer.detailed_analysis_to_file(date)
    analyzer.analyze(date)

