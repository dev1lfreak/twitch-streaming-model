class Player:
    def __init__(self, config):
        self.cfg = config
        self.video_buffer = [] # Список пакетов (отсортирован по PTS)
        self.audio_buffer = []
        self.av_sync_threshold = 40
        self.initial_buffer_duration = 2.0
        self.clock = 0
        self.is_stalled = True
        self.last_video_pts = -1
        self.last_audio_pts = -1

    def add_packet(self, packet):
        target_buffer = self.video_buffer if packet.type == 'video' else self.audio_buffer
        target_buffer.append(packet)
        target_buffer.sort(key=lambda p: p.pts)

    def get_buffer_level(self):
        if not self.video_buffer: return 0
        return self.video_buffer[-1].pts - self.clock

    def update(self, dt):
        if self.is_stalled:
            if self.get_buffer_level() >= self.initial_buffer_duration:
                self.is_stalled = False
                if self.video_buffer:
                    self.clock = self.video_buffer[0].pts
                return "playing" 
            else:
                return "stalling"

        self.clock += dt
        
        video_ready = [p for p in self.video_buffer if p.pts <= self.clock]
        audio_ready = [p for p in self.audio_buffer if p.pts <= self.clock]

        if not video_ready and not audio_ready:
            self.is_stalled = True
            return "stall_started"

        current_v_pts = self.last_video_pts
        if video_ready:
            current_v_pts = video_ready[-1].pts
            self.video_buffer = [p for p in self.video_buffer if p.pts > current_v_pts]
            self.last_video_pts = current_v_pts

        current_a_pts = self.last_audio_pts
        if audio_ready:
            current_a_pts = audio_ready[-1].pts
            self.audio_buffer = [p for p in self.audio_buffer if p.pts > current_a_pts]
            self.last_audio_pts = current_a_pts

        sync_diff = abs(current_v_pts - current_a_pts)
        if sync_diff > (self.av_sync_threshold / 1000.0):
            return ("sync_error", sync_diff)
            
        return "playing" 