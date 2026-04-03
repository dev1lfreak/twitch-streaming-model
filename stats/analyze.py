import os
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

class SimulationAnalyzer:
    def __init__(self):
        self.runs_data = []

    def save_run(self, stats_collector):
        run_results = {
            'buffer_levels': stats_collector.buffer_levels,
            'avg_stall_duration': np.mean(stats_collector.stalls) if stats_collector.stalls else 0,
            'packet_count': stats_collector.packet_count,
            'packet_loss': stats_collector.packet_loss,
            'sync_errors': [err * 1000 for err in stats_collector.sync_errors],
            'total_stall_time': stats_collector.total_stall_time
        }
        self.runs_data.append(run_results)
    
    def _test_and_calculate(self, data, metric_name, f):
        """Проводит тесты и рассчитывает параметры на основе лучшего распределения"""
        data = np.array(data)
        data = data[data > 0]
        if len(data) < 5:
            f.write("  Ошибка: Недостаточно данных для анализа.\n")
            return

        dist_configs = {
            'norm': {'name': 'Нормальное', 'func': stats.norm},
            'expon': {'name': 'Экспоненциальное', 'func': stats.expon},
            'lognorm': {'name': 'Логнормальное', 'func': stats.lognorm},
            'uniform': {'name': 'Равномерное', 'func': stats.uniform}
        }

        best_p = -1
        best_dist_name = ""
        best_dist_code = ""
        best_params = None

        f.write("Тесты на распределения:\n")
        for code, config in dist_configs.items():
            params = config['func'].fit(data)
            ks_stat, p_val = stats.kstest(data, code, args=params)
            status = "Подходит" if p_val > 0.05 else "Не подходит"
            f.write(f"  - {config['name']:18}: p-value = {p_val:.4f} ({status})\n")
            
            if p_val > best_p:
                best_p = p_val
                best_dist_name = config['name']
                best_dist_code = code
                best_params = params

        f.write(f"\n  Наиболее вероятный вид: {best_dist_name}\n")
        f.write("Параметры распределения: \n")

        dist_obj = dist_configs[best_dist_code]['func']
        
        mean, var = dist_obj.stats(*best_params, moments='mv')
        std_dev = np.sqrt(var)

        conf_int = dist_obj.interval(0.95, *best_params)

        f.write(f"  - Мат. ожидание:   {mean:.4f}\n")
        f.write(f"  - Дисперсия:       {var:.4f}\n")
        f.write(f"  - СКО:         {std_dev:.4f}\n")
        f.write(f"  - Дов. интервал 95%:   [{conf_int[0]:.6f}, {conf_int[1]:.6f}]\n")

    def detailed_analysis_to_file(self, date, scenario_id=1):
        if not self.runs_data: return

        filename = f"full_stat_report_{date.strftime('%Y%m%d_%H%M%S')}_scen_{scenario_id}.txt"
        full_path = os.path.join('results\\stats', filename)

        metrics = {
            "Ошибки синхронизации (ms)": [err for r in self.runs_data for err in r['sync_errors']],
            "Уровни буфера (s)": [lvl for r in self.runs_data for lvl in r['buffer_levels']],
            "Длительность рывков (ms)": [r['avg_stall_duration'] for r in self.runs_data]
        }

        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(f"#####Статистический анализ (Сценарий {scenario_id})#####\n")

            for metric_name, data in metrics.items():
                f.write("\n" + "_"*50 + "\n")
                f.write(f"\nМетрика: {metric_name}\n\n")
                self._test_and_calculate(data, metric_name, f)

        print(f"Подробный отчет сформирован: {full_path}")

    def analyze(self, date, scenario_id=1):
        if not self.runs_data:
            print("Нет данных для анализа.")
            return

        metrics_to_plot = {
            'sync_errors': {
                'data': [err for r in self.runs_data for err in r['sync_errors']],
                'title': 'Распределение ошибок синхронизации',
                'xlabel': 'Задержка (мс)',
                'color': 'skyblue'
            },
            'stalls': {
                'data': [r['avg_stall_duration'] for r in self.runs_data],
                'title': 'Распределение длительности рывков',
                'xlabel': 'Длительность (с)',
                'color': 'salmon'
            },
            'buffer_levels': {
                'data': [lvl for r in self.runs_data for lvl in r['buffer_levels']],
                'title': 'Распределение уровня буфера',
                'xlabel': 'Уровень заполнености (с)',
                'color': 'lightgreen'
            }
        }

        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        fig.suptitle(f'Статистический анализ симуляции (Сценарий {scenario_id})', fontsize=16)

        for ax, (key, cfg) in zip(axes, metrics_to_plot.items()):
            data = np.array(cfg['data'])
            # Фильтруем данные (например, для рывков важны только значения > 0)
            plot_data = data[data > 0] if key != 'buffer_levels' else data
            
            if len(plot_data) > 0:
                ax.hist(plot_data, bins=30, color=cfg['color'], edgecolor='black', alpha=0.7)
                ax.set_title(cfg['title'])
                ax.set_xlabel(cfg['xlabel'])
                ax.set_ylabel('Частота')
                ax.grid(axis='y', linestyle='--', alpha=0.7)
            else:
                ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center')
                ax.set_title(cfg['title'])

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        
        timestamp = date.strftime("%Y%m%d_%H%M%S")
        filename = f"exp_{timestamp}_scen_{scenario_id}.png"
        full_path = os.path.join('results\\graphics', filename)
        
        plt.savefig(full_path)
        plt.close()
        print(f"Гистограммы успешно сохранены в файл: {full_path}")

    def get_average_metrics(self):
        if not self.runs_data:
            return 0.0, 0.0
            
        avg_stall = sum(run['total_stall_time'] for run in self.runs_data) / len(self.runs_data)
        
        total_sync_per_run = [sum(run['sync_errors']) for run in self.runs_data]
        avg_sync = sum(total_sync_per_run) / len(self.runs_data)
        
        return avg_stall, avg_sync

    def clear_data(self):
        self.runs_data = []