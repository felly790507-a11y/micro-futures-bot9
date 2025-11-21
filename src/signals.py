# src/signal.py
from collections import deque
from dataclasses import dataclass

@dataclass
class KBar:
    ts: float
    open: float
    high: float
    low: float
    close: float
    vol: int

class KBarAggregator:
    def __init__(self, n=3):
        self.n = n
        self.buf = deque()

    def add_tick(self, tick):
        self.buf.append(tick)
        if len(self.buf) >= self.n:
            prices = [self.buf[i].price for i in range(self.n)]
            vols = [self.buf[i].qty for i in range(self.n)]
            kb = KBar(ts=self.buf[0].ts, open=prices[0], high=max(prices), low=min(prices), close=prices[-1], vol=sum(vols))
            for _ in range(self.n):
                self.buf.popleft()
            return kb
        return None

class TwoTickDetector:
    def __init__(self):
        self.recent = deque(maxlen=4)

    def on_tick(self, tick):
        self.recent.append(tick)

    def two_rise(self):
        if len(self.recent) < 2: return False
        return self.recent[-2].price < self.recent[-1].price

    def two_fall(self):
        if len(self.recent) < 2: return False
        return self.recent[-2].price > self.recent[-1].price
