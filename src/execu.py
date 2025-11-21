# src/execu.py
import asyncio
from loguru import logger

class ExecutorShioaji:
    def __init__(self, cfg, api):
        self.cfg = cfg
        self.api = api

    async def send_ioc(self, side, price, qty):
        # 這裡示範同步呼叫包到非阻塞執行緒或直接呼叫視你程式架構
        try:
            # 依你 shioaji 版本填寫正確下單呼叫
            # ex: order = self.api.order(..., price=price, qty=qty, ioc=True)
            # return {"filled_qty": filled, "avg_price": avg}
            pass
        except Exception as e:
            print("Shioaji 下單錯誤:", e)
            return {"filled_qty": 0, "avg_price": price}

