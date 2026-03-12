class Network:
    def __init__(self, config, generator):
        self.cfg = config
        self.generator = generator
        self.last_departure_time = 0
        self.packet_loss = 0

    def process_packet(self, packet, current_time):
        if self.generator.random() < self.cfg['packet_loss_probability']:
            self.packet_loss += 1
            return None

        transmission_delay = (packet.size_bytes * 8) / (self.cfg['bandwidth'] * 1024)
        
        arrival_at_router = max(current_time, self.last_departure_time)
        wait_in_queue = arrival_at_router - current_time
        
        if wait_in_queue > 0.05: # Условный буфер роутера на 50мс
            self.packet_loss += 1
            return None

        jitter = self.generator.expovariate(1.0 / self.cfg['jitter_intensity'])
        
        delivery_time = arrival_at_router + transmission_delay + self.cfg['network_delay'] + jitter
        self.last_departure_time = arrival_at_router + transmission_delay
        
        packet.arrival_time = delivery_time
        return packet
    
    def get_packet_loss(self):
        return self.packet_loss