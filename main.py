import random, heapq
from blocks.streamer import Streamer
from blocks.network import NetworkChannel
from blocks.player import Player
from model.statistics_collector import StatisticsCollector

def run_simulation(duration=20):
    stats = StatisticsCollector()
    streamer = Streamer()
    net = NetworkChannel(bandwidth=4000000, loss_rate=0.005)
    player = Player(start_threshold=2.0)
    
    events = [] # (time, action, data)
    heapq.heappush(events, (0, "gen_v", None))
    heapq.heappush(events, (0, "gen_a", None))
    heapq.heappush(events, (0, "tick", None))
    
    stats.log_stall_start(0) # Стартовая буферизация

    while events:
        t, action, data = heapq.heappop(events)
        if t > duration: break

        if action == "gen_v":
            frame = streamer.get_frame(t)
            arrival = net.process(frame, t, stats)
            if arrival: heapq.heappush(events, (arrival, "recv", frame))
            heapq.heappush(events, (t + 1/60, "gen_v", None))

        elif action == "gen_a":
            frame = streamer.get_audio(t)
            arrival = net.process(frame, t, stats)
            if arrival: heapq.heappush(events, (arrival, "recv", frame))
            heapq.heappush(events, (t + 0.02, "gen_a", None))

        elif action == "recv":
            if data["type"] == "v": player.buf_v.append(data["pts"])
            else: player.buf_a.append(data["pts"])

        elif action == "tick":
            player.update(t, 0.01, stats)
            heapq.heappush(events, (t + 0.01, "tick", None))

    stats.report()

run_simulation(20000)