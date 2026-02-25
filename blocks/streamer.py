import random

class Streamer:
    def __init__(self, fps=60, gop=120):
        self.fps = fps
        self.gop = gop
        self.count = 0

    def get_frame(self, now):
        self.count += 1
        is_i = (self.count % self.gop == 0)
        # Видео: Pareto для I-кадров, Normal для P-кадров
        size = int(random.paretovariate(3) * 50000) if is_i else int(random.normalvariate(8000, 800))
        return {"type": "v", "pts": now, "size": size}

    def get_audio(self, now):
        # Аудио: константный размер (CBR)
        return {"type": "a", "pts": now, "size": 400}