import math

class QoEEvaluator:
    def __init__(self, alpha=100, beta=2, gamma=5):
        self.alpha = alpha   # 100% качества видео
        self.beta = beta     # Штраф в % за рывки
        self.gamma = gamma   # Штраф в % за рассинхрон
        self.v_max = 7000    # Максимальный исследуемый битрейт для нормализации

    def check_constraints(self, config):
        V = config.get('video_bitrate', 0)
        G = config.get('gop_size', 0)
        B = config.get('bandwidth', 0)
        J = config.get('jitter_intensity', 0)
        P = config.get('packet_loss_probability', 0)

        if not (2500 < V < 7000): return False
        if not (50 < G < 300): return False
        if not (3000 < B < 7500): return False
        if not (0.005 < J < 0.05): return False
        if not (0 < P < 0.05): return False

        return True

    def calculate(self, bitrate, total_stall, total_sync_error):
        if bitrate <= 0: return float('-inf')

        quality_base = self.alpha * (math.log(bitrate) / math.log(self.v_max))
        stall_penalty = self.beta * total_stall
        sync_penalty = self.gamma * total_sync_error / 1000
        
        qoe = quality_base - stall_penalty - sync_penalty
        print(f"QoE Calculation: QoE={qoe:.2f}")
        if qoe < 0: qoe = 0
        return qoe