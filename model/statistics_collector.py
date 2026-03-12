class StatisticsCollector:
    def __init__(self):
        self.timestamps = []
        self.buffer_levels = []
        self.stalls = []           # Список длительностей каждого рывка
        self.sync_errors = []      # Список величин рассинхрона (в сек)
        self.packet_loss = 0
        self.packet_count = 0
        
        self.total_stall_time = 0
        self.is_currently_stalling = True # Начинаем с буферизации
        self.stall_start_time = 0

    def collect(self, time, buffer_lvl, status):
        self.timestamps.append(time)
        self.buffer_levels.append(buffer_lvl)
        
        if status == "stalling" or status == "stall_started":
            if not self.is_currently_stalling:
                self.is_currently_stalling = True
                self.stall_start_time = time
        else:
            if self.is_currently_stalling:
                self.is_currently_stalling = False
                duration = time - self.stall_start_time
                if duration > 0:
                    self.stalls.append(duration)
                    self.total_stall_time += duration

    def add_sync_error(self, time, diff):
        self.sync_errors.append(diff)

    def set_packet_loss(self, count):
        self.packet_loss += count
    
    def set_packet_count(self, count):
        self.packet_count = count

    def print_report(self):
        duration = self.timestamps[-1] if self.timestamps else 0
        stall_count = len(self.stalls)
        avg_stall_duration = (sum(self.stalls) / stall_count) if stall_count > 0 else 0
        avg_buffer = sum(self.buffer_levels) / len(self.buffer_levels) if self.buffer_levels else 0
        stall_ratio = (self.total_stall_time / duration * 100) if duration > 0 else 0
        
        max_sync = max(self.sync_errors) * 1000 if self.sync_errors else 0
        avg_sync = (sum(self.sync_errors) / len(self.sync_errors) * 1000) if self.sync_errors else 0

        print("\n" + "_"*40)
        print(" Отчёт имитационной модели Twitch ")
        print("_"*40)
        
        print(f"Общее время симуляции:    {duration:.2f} сек")
        print(f"Макс. уровень буфера:    {max(self.buffer_levels):.2f} сек")
        print(f"Средний уровень буфера:   {avg_buffer:.2f} сек")
        
        print("_" * 40)
        print(f"Количество рывков (Stalls): {stall_count}")
        print(f"Общее время ожидания:      {self.total_stall_time:.2f} сек")
        print(f"Stall Ratio (простой):     {stall_ratio:.2f}%")
        print(f"Средняя длительность рывка: {avg_stall_duration:.2f} сек")
        
        print("_" * 40)

        print(f"Общее количество пакетов: {self.packet_count}")
        print(f"Потеря пакетов: {self.packet_loss}")
        print(f"Процент потерь: {self.packet_loss / self.packet_count * 100:.2f}%" if self.packet_count > 0 else "N/A")
        print(f"Синхронизация (A/V Sync):")
        if self.sync_errors:
            print(f"  - Макс. рассинхрон:      {max_sync:.2f} мс")
            print(f"  - Средний рассинхрон:    {avg_sync:.2f} мс")
            print(f"  - Кол-во ошибок синхронизации: {len(self.sync_errors)}")
        else:
            print("  - Ошибок синхронизации не выявлено")
            
        print('\n')