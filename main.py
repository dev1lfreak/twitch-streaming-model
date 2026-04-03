from datetime import datetime
import json
import numpy as np

from model.simulator import Simulation
from stats.analyze import SimulationAnalyzer
from stats.data_exporter import DataExporter
from stats.sensitivity_analyzer import SensitivityAnalyzer
from stats.qoe_evaluator import QoEEvaluator
from stats.optimizer import SimulationOptimizer

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
    base_config = load_simulation_config('configs/new_standard_conf.json')
    if not base_config: exit(1)

    evaluator = QoEEvaluator()
    optimizer = SimulationOptimizer(base_config, evaluator)
    plotter = SensitivityAnalyzer(base_config)

    history, best_result = optimizer.run_random_search(num_combinations=50, runs_per_combination=5)
    
    print("\n\t\tЛучший результат оптимизации:")
    print(best_result['config'])
    print(f"Итоговый QoE: {best_result['qoe']:.2f}")

    plotter.plot_3d_qoe(history)
    plotter.plot_2d_scatter_grid(history)

    # param_ranges = {
    #     'video_bitrate': np.linspace(2505, 6995, 10),
    #     'bandwidth': np.linspace(3005, 6995, 10),
    #     'gop_size': np.linspace(55, 295, 10, dtype=int),
    #     'jitter_intensity': np.linspace(0.002, 0.048, 10),
    #     'packet_loss_probability': np.linspace(0.001, 0.048, 10)
    # }
    
    # isolated_data = optimizer.run_isolated_analysis(param_ranges, runs_per_point=10)
    
    print("\nВсе тесты завершены. Графики сохранены в папке results/optimization/")
