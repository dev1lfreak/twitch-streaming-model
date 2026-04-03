import csv
import os
from datetime import datetime

class DataExporter:
    @staticmethod
    def export_to_csv(runs_data, date ,scenario_id=1):
        if not runs_data:
            print("Нет данных для экспорта.")
            return

        timestamp = date.strftime("%Y%m%d_%H%M%S")
        filename = f"exp_{timestamp}_scen_{scenario_id}.csv"
        full_path = os.path.join('results\\data', filename)

        keys = runs_data[0].keys()

        try:
            with open(full_path, 'w', newline='', encoding='utf-8') as output_file:
                dict_writer = csv.DictWriter(output_file, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(runs_data)
            print(f"Данные успешно экспортированы в: {filename}")
        except IOError as e:
            print(f"Ошибка при записи файла: {e}")
    
    def export_optimization_results(self, history, best_config, filename="optimization_results.csv"):
        
        os.makedirs('results/optimization', exist_ok=True)
        filepath = f'results/optimization/{datetime.now().strftime("%Y%m%d_%H%M")}_{filename}'
        
        with open(filepath, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['Video Bitrate', 'Buffer Duration', 'GOP Size', 'Avg Stall (s)', 'Avg Sync Error', 'QoE Score', 'Is Best'])
            
            for item in history:
                cfg = item['config']
                is_best = "YES" if item == best_config else ""
                
                writer.writerow([
                    cfg['video_bitrate'],
                    cfg['initial_buffer_duration'],
                    cfg['gop_size'],
                    round(item['avg_stall'], 3),
                    round(item['avg_sync_error'], 3),
                    round(item['qoe'], 3),
                    is_best
                ])
        print(f"Таблица с результатами оптимизации сохранена в {filepath}")