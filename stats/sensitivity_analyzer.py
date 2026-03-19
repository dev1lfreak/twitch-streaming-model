import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from model.simulator import Simulation

class SensitivityAnalyzer:
    def __init__(self, base_config):
        self.base_config = base_config
        self.results = {}

    def run_sensitivity_test(self, param_name, values, iterations_per_step=10):
        print(f"Запуск анализа чувствительности для параметра: {param_name}")
        param_results = []

        for val in values:
            current_config = self.base_config.copy()
            current_config[param_name] = val
            
            run_metrics = {
                'avg_buffer': [],
                'total_stall_time': [],
                'avg_sync': [],
                'sync_count': []
            }

            for i in range(iterations_per_step):
                sim = Simulation(current_config)
                sim.run(3000)
                
                run_metrics['avg_buffer'].append(np.mean(sim.stats.buffer_levels))
                run_metrics['total_stall_time'].append(sim.stats.total_stall_time)
                sync_errs = [abs(e) * 1000 for e in sim.stats.sync_errors]
                run_metrics['avg_sync'].append(np.mean(sync_errs) if sync_errs else 0)
                run_metrics['sync_count'].append(len(sync_errs))

            step_summary = {
                'value': val,
                'avg_buffer': np.mean(run_metrics['avg_buffer']),
                'total_stall_time': np.mean(run_metrics['total_stall_time']),
                'avg_sync': np.mean(run_metrics['avg_sync']),
                'sync_count': np.mean(run_metrics['sync_count'])
            }
            param_results.append(step_summary)
            print(f"  Готово для {param_name} = {val}")

        self.results[param_name] = param_results

    def plot_heatmap(self, param_name):
        if param_name not in self.results:
            return

        data = self.results[param_name]
        
        matrix_data = []
        labels = []
        for item in data:
            matrix_data.append([item['avg_buffer'], item['total_stall_time'], item['avg_sync']])
            labels.append(item['value'])

        matrix_data = np.array(matrix_data)

        norm_data = (matrix_data - matrix_data.min(axis=0)) / (matrix_data.max(axis=0) - matrix_data.min(axis=0) + 1e-9)

        plt.figure(figsize=(10, 8))
        sns.heatmap(norm_data, annot=matrix_data, fmt=".2f", 
                    xticklabels=['Buffer Level', 'Total Stalls', 'AV Sync Error'],
                    yticklabels=labels, cmap='YlGnBu')
        
        plt.title(f"Влияние {param_name} на метрики качества (Heatmap)")
        plt.ylabel(f"Значение входного параметра: {param_name}")
        
        os.makedirs('results/sensitivity', exist_ok=True)
        plt.savefig(f'results/sensitivity/heatmap_{param_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        plt.close()

    def plot_dependency(self, param_name):
        data = self.results[param_name]
        x = [item['value'] for item in data]
        
        fig, ax1 = plt.subplots(figsize=(10, 6))

        color = 'tab:blue'
        ax1.set_xlabel(param_name)
        ax1.set_ylabel('Время рывков (с)', color=color)
        ax1.plot(x, [item['total_stall_time'] for item in data], color=color, marker='o', label='Stall Time')
        ax1.tick_params(axis='y', labelcolor=color)

        ax2 = ax1.twinx()
        color = 'tab:green'
        ax2.set_ylabel('Среднее отклонение синхронизации (мс)', color=color)
        ax2.plot(x, [item['avg_sync'] for item in data], color=color, marker='s', label='Sync Error')
        ax2.tick_params(axis='y', labelcolor=color)

        plt.title(f"Зависимость QoS от {param_name}")
        plt.grid(True, alpha=0.3)
        plt.savefig(f'results/sensitivity/lines_{param_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
        plt.close()