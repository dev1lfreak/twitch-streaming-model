import csv
import os

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