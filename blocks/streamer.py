from entities.packet import Packet
from entities.frame import Frame

class Streamer:
    def __init__(self, config, generator):
        self.cfg = config
        self.generator = generator
        self.frame_count = 0
        self.packet_count = 0
        
    def generate_video_frame(self, current_time):
        is_key = (self.frame_count % self.cfg['gop_size']) == 0
        self.frame_count += 1
        
        if is_key:
            # Распределение Парето для тяжелых I-кадров
            size = (self.generator.paretovariate(2.5) + 1) * (self.cfg['video_bitrate'] / self.cfg['fps'] / 8) * 1024
        else:
            # Нормальное распределение для P-кадров
            mean_size = self.cfg['video_bitrate'] / self.cfg['fps'] / 8 * 1024 / 6
            size = max(512, self.generator.gauss(mean_size, mean_size * 0.2))
        frame = Frame('video', current_time, size, is_key)    
        return frame
    
    def generate_audio_frame(self, current_time):
        duration = 0.01 
        mean_size = (self.cfg['audio_bitrate'] * 1000 * duration) / 8
        
        variation = 0.1
        min_size = mean_size * (1 - variation)
        max_size = mean_size * (1 + variation)
        
        size = self.generator.uniform(min_size, max_size)
        frame = Frame('audio', current_time, size)
        
        return frame

    def fragment_into_packets(self, frame, send_time):
        mtu = 1500
        packets = []
        remaining = frame.size
        
        while remaining > 0:
            p_size = min(remaining, mtu)
            packets.append(Packet(frame.type, frame.pts, p_size, send_time))
            self.packet_count += 1
            remaining -= p_size
            send_time += 0.001 
        return packets
    
    def get_frame_count(self):
        return self.frame_count

    def get_packet_count(self):
        return self.packet_count