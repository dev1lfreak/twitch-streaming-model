import heapq
from blocks.streamer import Streamer
from blocks.network import Network
from blocks.player import Player
from model.statistics_collector import StatisticsCollector
from model.generator import MersenneTwister

class Simulation:
    def __init__(self, config):
        self.events = [] 
        self.config = config
        self.generator = MersenneTwister()
        self.streamer = Streamer(config, self.generator)
        self.network = Network(config, self.generator)
        self.player = Player(config)
        self.stats = StatisticsCollector()
        self.fps = 60
        self.curr_time = 0
        self.counter = 0

    def add_event(self, time, event_type, data=None):
        heapq.heappush(self.events, (time, self.counter, event_type, data))
        self.counter += 1

    def run(self, duration):
        self.add_event(0, "gen_video")
        self.add_event(0, "gen_audio")
        self.add_event(0, "player_tick")

        while self.events and self.curr_time < duration:
            time, _, etype, data = heapq.heappop(self.events) 
            self.curr_time = time
            
            if etype == "gen_video":
                frame = self.streamer.generate_video_frame(time)
                pkts = self.streamer.fragment_into_packets(frame, time)
                for p in pkts:
                    self.add_event(p.send_time, "network_ingress", p)
                self.add_event(time + 1/self.fps, "gen_video")

            elif etype == "gen_audio":
                frame = self.streamer.generate_audio_frame(time)
                pkts = self.streamer.fragment_into_packets(frame, time)
                for p in pkts:
                    self.add_event(p.send_time, "network_ingress", p)
                self.add_event(time + 0.01, "gen_audio")

            elif etype == "network_ingress":
                delivered_pkt = self.network.process_packet(data, time)
                if delivered_pkt:
                    self.add_event(delivered_pkt.arrival_time, "player_recv", delivered_pkt)

            elif etype == "player_recv":
                self.player.add_packet(data)

            elif etype == "player_tick":
                res = self.player.update(0.01)
        
                self.stats.collect(time, self.player.get_buffer_level(), res)
                
                if isinstance(res, tuple) and res[0] == "sync_error":
                    self.stats.add_sync_error(time, res[1])   
                self.add_event(time + 0.01, "player_tick")

        self.stats.set_packet_count(self.streamer.get_packet_count())     
        self.stats.set_packet_loss(self.network.get_packet_loss())
        self.stats.print_report()