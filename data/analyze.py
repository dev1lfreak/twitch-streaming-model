import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

class SimulationAnalyzer:
    def __init__(self):
        self.runs_data = []

    def save_run(self, stats_collector):
        run_results = {
            'max_buffer': max(stats_collector.buffer_levels) if stats_collector.buffer_levels else 0,
            'avg_buffer': np.mean(stats_collector.buffer_levels) if stats_collector.buffer_levels else 0,
            'stall_count': len(stats_collector.stalls),
            'total_stall_time': stats_collector.total_stall_time,
            'avg_stall_duration': np.mean(stats_collector.stalls) if stats_collector.stalls else 0,
            'packet_count': stats_collector.packet_count,
            'packet_loss': stats_collector.packet_loss,
            'max_sync': max(stats_collector.sync_errors) * 1000 if stats_collector.sync_errors else 0,
            'avg_sync': np.mean(stats_collector.sync_errors) * 1000 if stats_collector.sync_errors else 0
        }
        self.runs_data.append(run_results)

    def analyze(self):
        if not self.runs_data:
            print("Нет данных для анализа.")
            return

        metrics = self.runs_data[0].keys()
        summary = {}

        print("\n" + "Статистический анализ".center(60, "="))
        
        for key in metrics:
            values = [run[key] for run in self.runs_data]
            mean_val = np.mean(values)
            std_val = np.std(values)
            summary[key] = values
            
            print(f"{key:20} | M[X]: {mean_val:10.4f} | σ: {std_val:10.4f}")

        self._plot_results(summary)
        self._detect_distributions(summary)

    def _detect_distributions(self, summary):
        """Распознавание вида распределения для ключевых метрик"""
        print("\n" + " ПРОВЕРКА ВИДА РАСПРЕДЕЛЕНИЯ ".center(60, "="))
        
        target_metrics = ['avg_buffer', 'total_stall_time', 'packet_loss']
        
        for metric in target_metrics:
            data = np.array(summary[metric])
            if np.all(data == data[0]):
                print(f"{metric:20}: Константа")
                continue

            # Тест Шапиро-Уилка на нормальность
            _, p_norm = stats.shapiro(data)
            
            if p_norm > 0.05:
                dist_name = "Нормальное (Gaussian)"
            else:
                # Пробуем экспоненциальное
                _, p_exp = stats.ks_2samp(data, stats.expon.rvs(size=len(data), loc=np.mean(data)))
                dist_name = "Экспоненциальное" if p_exp > 0.05 else "Неизвестное/Сложное"
            
            print(f"{metric:20}: {dist_name} (p-value: {p_norm:.4f})")

    def _plot_results(self, summary):
        plt.figure(figsize=(15, 10))
        
        plot_map = {
            'avg_buffer': (2, 2, 1, 'Средний буфер (сек)', 'blue'),
            'total_stall_time': (2, 2, 2, 'Общее время рывков (сек)', 'red'),
            'packet_loss': (2, 2, 3, 'Потери пакетов (шт)', 'green'),
            'avg_sync': (2, 2, 4, 'Средний рассинхрон (мс)', 'orange')
        }

        for key, (r, c, i, title, color) in plot_map.items():
            plt.subplot(r, c, i)
            plt.hist(summary[key], bins=15, color=color, alpha=0.7, edgecolor='black')
            plt.title(title)
            plt.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        plt.show()
