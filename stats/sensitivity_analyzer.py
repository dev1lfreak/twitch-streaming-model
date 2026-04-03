import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
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

    def plot_3d_qoe(self, history):
        """3D график: X=loss, Y=gop, Z=jitter, Цвет=QoE"""
        P = [item['config']['packet_loss_probability'] for item in history]
        G = [item['config']['gop_size'] for item in history]
        J = [item['config']['jitter_intensity'] for item in history]
        Q = [item['qoe'] for item in history]

        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        scatter = ax.scatter(P, G, J, c=Q, cmap='plasma', s=80, alpha=0.8, edgecolor='k')
        cbar = plt.colorbar(scatter, ax=ax, pad=0.1)
        cbar.set_label('QoE Score')

        ax.set_xlabel('Packet Loss Prob')
        ax.set_ylabel('GOP Size')
        ax.set_zlabel('Jitter Intensity')
        plt.title('3D Зависимость QoE от сетевых метрик и GOP')

        os.makedirs('results/optimization', exist_ok=True)
        plt.savefig(f'results/optimization/3d_qoe_{datetime.now().strftime("%H%M%S")}.png')
        plt.close()

    def plot_2d_scatter_grid(self, history):
        """Строит 2D графики зависимости QoE от всех 5 параметров (в виде облака точек)"""
        params = ['video_bitrate', 'bandwidth', 'gop_size', 'jitter_intensity', 'packet_loss_probability']
        fig, axes = plt.subplots(2, 3, figsize=(16, 10))
        axes = axes.flatten()

        Q = [item['qoe'] for item in history]

        for i, param in enumerate(params):
            X = [item['config'][param] for item in history]
            axes[i].scatter(X, Q, alpha=0.6, c='blue', edgecolor='k')
            axes[i].set_xlabel(param)
            axes[i].set_ylabel('QoE Score')
            axes[i].grid(True, linestyle='--', alpha=0.5)

        axes[-1].axis('off')
        plt.tight_layout()
        plt.savefig(f'results/optimization/2d_scatter_grid_{datetime.now().strftime("%H%M%S")}.png')
        plt.close()

    def plot_isolated_dependencies(self, isolated_results, param_name):
        """Графики для сценария поочередного изменения (линейные)"""
        fig, axes = plt.subplots(figsize=(8, 6))

        for i, (param, data) in enumerate(isolated_results.items()):
            if not data or (param != param_name): continue
            X = [pt[0] for pt in data]
            Y = [pt[1] for pt in data]
            
            axes.plot(X, Y, marker='o', linestyle='-', color='green', linewidth=2)
            axes.set_xlabel(param)
            axes.set_ylabel('QoE Score')
            axes.set_title(f'Влияние {param} на QoE\n(остальные константа)')
            axes.grid(True)

        plt.tight_layout()
        plt.savefig(f'results/optimization/isolated/isolated_{param}_{datetime.now().strftime("%H%M%S")}.png')
        plt.close()