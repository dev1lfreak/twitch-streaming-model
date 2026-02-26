class StatisticsCollector:
    def __init__(self):
        self.stalls = []                # Список (start_time, duration)
        self.current_stall_start = None
        self.initial_buffer_time = 0
        self.packet_loss_count = 0
        self.desync_values = []         # Список значений |A_pts - V_pts|
        self.total_packets = 0

    def log_stall_start(self, time):
        if self.current_stall_start is None:
            self.current_stall_start = time

    def log_stall_end(self, time):
        if self.current_stall_start is not None:
            duration = time - self.current_stall_start
            if self.initial_buffer_time == 0:
                self.initial_buffer_time = duration
            else:
                self.stalls.append((self.current_stall_start, duration))
            self.current_stall_start = None

    def log_loss(self):
        self.packet_loss_count += 1

    def log_desync(self, value):
        self.desync_values.append(value)

    def report(self):
        print("\n" + "="*30)
        print("ОТЧЕТ О КАЧЕСТВЕ (QoE)")
        print("="*30)
        print(f"Задержка при старте: {self.initial_buffer_time:.2f} сек")
        print(f"Количество рывков: {len(self.stalls)}")
        if self.stalls:
            avg_stall = sum(d for t, d in self.stalls) / len(self.stalls)
            print(f"Средняя длительность рывка: {avg_stall:.2f} сек")
        
        loss_p = (self.packet_loss_count / self.total_packets * 100) if self.total_packets else 0
        print(f"Потери пакетов: {self.packet_loss_count} ({loss_p:.2f}%)")
        
        if self.desync_values:
            avg_desync = sum(self.desync_values) / len(self.desync_values)
            print(f"Средняя рассинхронизация: {avg_desync*1000:.1f} мс")
        print("="*30)