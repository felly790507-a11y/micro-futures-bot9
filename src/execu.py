# src/execu.py
import asyncio
from loguru import logger

class ExecutorSim:
    def __init__(self, cfg):
        self.cfg = cfg

    async def send_ioc(self, side, price, qty):
        logger.info(f"[SIM] IOC {side} price={price} qty={qty}")
        await asyncio.sleep(0)  # simulate tiny latency
        filled = qty  # deterministic: fully filled in sim
        return {"filled_qty": filled, "avg_price": price}

# NOTE: 若要接 Shioaji，請在此新增 ExecutorShioaji class 實作 send_ioc 並呼叫 shioaji API
