# src/execu.py
import asyncio
from loguru import logger

class ExecutorShioaji:
    def __init__(self, cfg, api):
        self.cfg = cfg
        self.api = api

    async def send_ioc(self, side, price, qty):
        # ?ㄐ蝷箇??郊?澆??憛銵???亙?怨?雿?撘瑽?
        try:
            # 靘? shioaji ?憛怠神甇?Ⅱ銝?澆
            # ex: order = self.api.order(..., price=price, qty=qty, ioc=True)
            # return {"filled_qty": filled, "avg_price": avg}
            pass
        except Exception as e:
            print("Shioaji 銝?航炊:", e)
            return {"filled_qty": 0, "avg_price": price}

