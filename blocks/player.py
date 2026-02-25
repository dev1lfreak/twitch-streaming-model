class Player:
    def __init__(self, start_threshold=2.0):
        self.threshold = start_threshold
        self.buf_v = []
        self.buf_a = []
        self.playing = False
        self.clock = 0

    def update(self, now, dt, stats):
        # Считаем уровень буфера (самый старый PTS в очереди минус текущие часы)
        v_level = (max(self.buf_v) - self.clock) if self.buf_v else 0
        
        if not self.playing:
            if v_level >= self.threshold:
                self.playing = True
                stats.log_stall_end(now)
        else:
            if v_level <= 0:
                self.playing = False
                stats.log_stall_start(now)
            else:
                self.clock += dt
                # Считаем рассинхрон, если есть данные обоих типов
                if self.buf_v and self.buf_a:
                    desync = abs(min(self.buf_v) - min(self.buf_a))
                    stats.log_desync(desync)
                
                # Имитируем потребление кадров (удаляем старые PTS)
                self.buf_v = [p for p in self.buf_v if p > self.clock]
                self.buf_a = [p for p in self.buf_a if p > self.clock]