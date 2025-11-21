# src/strategy.py
import time
from loguru import logger
from src.signals import KBarAggregator, TwoTickDetector
from src.state import StrategyState

class TwoTickStrategy:
    def __init__(self, cfg, executor):
        self.cfg = cfg
        self.exec = executor
        self.agg = KBarAggregator(n=3)
        self.det = TwoTickDetector()
        self.state = StrategyState()
        self.cooldown = cfg.get("cooldown_secs", 0.5)
        self.last_action = 0.0

    async def on_tick(self, tick):
        now = time.time()
        self.det.on_tick(tick)
        kbar = self.agg.add_tick(tick)
        if now - self.last_action < self.cooldown:
            return
        # two-tick rise -> buy probe
        if self.det.two_rise():
            await self._on_two_rise(tick)
        elif self.det.two_fall():
            await self._on_two_fall(tick)

    async def _on_two_rise(self, tick):
        if self.state.position >= self.cfg["target_qty"]:
            return
        probe = max(1, int(self.cfg["target_qty"] * self.cfg.get("ioc_probe_ratio", 0.3)))
        resp = await self.exec.send_ioc("BUY", tick.price, probe)
        filled = resp.get("filled_qty", 0)
        if filled > 0:
            self.state.add_position(filled)
            logger.info(f"Bought {filled}, pos={self.state.position}")
            self.last_action = time.time()

    async def _on_two_fall(self, tick):
        if self.state.position <= 0:
            return
        qty = self.state.position
        resp = await self.exec.send_ioc("SELL", tick.price, qty)
        filled = resp.get("filled_qty", 0)
        if filled > 0:
            self.state.reduce_position(filled)
            logger.info(f"Sold {filled}, pos={self.state.position}")
            self.last_action = time.time()
