import math
import time

class MersenneTwister:
    def __init__(self, seed_value=None):
        self.w, self.n, self.m, self.r = 32, 624, 397, 31
        self.a = 0x9908B0DF
        self.u, self.d = 11, 0xFFFFFFFF
        self.s, self.b = 7, 0x9D2C5680
        self.t, self.c = 15, 0xEFC60000
        self.l = 18
        self.f = 1812433253
        
        self.MT = [0] * self.n
        self.index = self.n + 1
        self.lower_mask = (1 << self.r) - 1
        self.upper_mask = (~self.lower_mask) & 0xFFFFFFFF
        
        self.seed(seed_value if seed_value is not None else int(time.time()))

    def seed(self, seed_value):
        self.MT[0] = seed_value & 0xFFFFFFFF
        for i in range(1, self.n):
            self.MT[i] = (self.f * (self.MT[i-1] ^ (self.MT[i-1] >> (self.w - 2))) + i) & 0xFFFFFFFF
        self.index = self.n

    def _twist(self):
        """Перемешивание состояния (Twist)"""
        for i in range(self.n):
            x = (self.MT[i] & self.upper_mask) + (self.MT[(i + 1) % self.n] & self.lower_mask)
            xA = x >> 1
            if x % 2 != 0:
                xA = xA ^ self.a
            self.MT[i] = self.MT[(i + self.m) % self.n] ^ xA
        self.index = 0

    def random(self):
        """Базовый генератор [0.0, 1.0)"""
        if self.index >= self.n:
            self._twist()

        y = self.MT[self.index]
        y ^= (y >> self.u) & self.d
        y ^= (y << self.s) & self.b
        y ^= (y << self.t) & self.c
        y ^= (y >> self.l)
        
        self.index += 1
        return (y & 0xFFFFFFFF) / 4294967296.0

    def uniform(self, a, b):
        """Равномерное распределение для аудио"""
        return a + (b - a) * self.random()

    def expovariate(self, lambd):
        """Экспоненциальное распределение для джиттера (Метод обратной функции)"""
        return -math.log(1.0 - self.random()) / lambd

    def paretovariate(self, alpha):
        """Распределение Парето для I-кадров (Метод обратной функции)"""
        u = self.random()
        return 1.0 / pow(1.0 - u, 1.0 / alpha)

    def gauss(self, mu, sigma):
        """Нормальное распределение для P-кадров (Преобразование Бокса-Мюллера)"""
        u1 = self.random()
        u2 = self.random()
        if u1 <= 0.0: u1 = 1e-9 
        
        z0 = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return mu + z0 * sigma