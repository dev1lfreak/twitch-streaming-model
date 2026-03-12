class Frame:
    def __init__(self, type, pts, size, is_keyframe=False):
        self.type = type  # 'video' или 'audio'
        self.pts = pts    # Presentation Time Stamp (секунды)
        self.size = size
        self.is_keyframe = is_keyframe