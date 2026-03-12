class Packet:
    def __init__(self, type, pts, size_bytes, send_time):
        self.type = type
        self.pts = pts
        self.size_bytes = size_bytes
        self.send_time = send_time # время отправки
        self.arrival_time = 0 # время прибытия