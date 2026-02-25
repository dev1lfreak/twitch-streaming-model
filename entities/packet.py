class Packet:
    """Объект сетевого пакета (фрагмент кадра)"""
    def __init__(self, pts, media_type, payload_size, is_last):
        self.pts = pts                      # Копируем PTS из кадра для сортировки в буфере
        self.media_type = media_type        # 'video' или 'audio'
        self.payload_size = payload_size    # Размер полезной нагрузки (не более MTU)
        self.is_last = is_last              # Флаг: последний ли это пакет в кадре
        
        self.send_time = 0                  # Время отправки (t_send)
        self.arrival_time = 0               # Время получения (t_recv)

    def __repr__(self):
        # Для удобного вывода в консоль при отладке
        return f"[Packet {self.media_type}] PTS: {self.pts:.3f}s, Payload: {self.payload_size}"