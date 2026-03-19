from datetime import datetime
import json

from model.simulator import Simulation
from stats.analyze import SimulationAnalyzer
from stats.data_exporter import DataExporter
from stats.sensitivity_analyzer import SensitivityAnalyzer

def load_simulation_config(file_path):
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
    base_config = load_simulation_config('configs/standart_conf.json')
    s_analyzer = SensitivityAnalyzer(base_config)

    loss_values = [0, 0.001, 0.005, 0.01, 0.02, 0.05, 0.1]
    s_analyzer.run_sensitivity_test('packet_loss_probability', loss_values, iterations_per_step=10)
    
    s_analyzer.plot_heatmap('packet_loss_probability')
    s_analyzer.plot_dependency('packet_loss_probability')

    buffer_values = [0.5, 1.0, 1.5, 2.0, 3.0, 5.0]
    s_analyzer.run_sensitivity_test('initial_buffer_duration', buffer_values, iterations_per_step=10)
    
    s_analyzer.plot_heatmap('initial_buffer_duration')
    s_analyzer.plot_dependency('initial_buffer_duration')

