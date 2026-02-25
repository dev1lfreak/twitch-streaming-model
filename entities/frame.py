class Frame:
    """Объект кадра, генерируемый стримером"""
    def __init__(self, media_type, frame_type, pts, size, value):
        self.media_type = media_type    # 'video' или 'audio'
        self.frame_type = frame_type    # 'I', 'P' (для видео) или None (для аудио)
        self.pts = pts                  # Presentation Time Stamp (в секундах)
        self.size = size                # Размер кадра в байтах
        self.value = value              # Динамика сцены (число) или громкость

    def __repr__(self):
        # Для удобного вывода в консоль при отладке
        type_str = f"{self.media_type}_{self.frame_type}" if self.frame_type else self.media_type
        return f"[Frame {type_str}] PTS: {self.pts:.3f}s, Size: {self.size} bytes"