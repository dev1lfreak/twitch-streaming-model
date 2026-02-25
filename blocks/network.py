import random

class NetworkChannel:
    def __init__(self, bandwidth=5000000, loss_rate=0.01):
        self.bw = bandwidth # бит/с
        self.loss_rate = loss_rate
        self.busy_until = 0

    def process(self, packet, now, stats):
        stats.total_packets += 1
        if random.random() < self.loss_rate:
            stats.log_loss()
            return None
        
        # Упрощенная модель очереди (FIFO)
        transmit_time = (packet["size"] * 8) / self.bw
        start_time = max(now, self.busy_until)
        self.busy_until = start_time + transmit_time
        
        # Пинг + Экспоненциальный джиттер
        arrival = self.busy_until + 0.03 + random.expovariate(1/0.01)
        return arrival