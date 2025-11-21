# src/state.py
from typing import Dict, Any
from threading import Lock

class StrategyState:
    """
    StrategyState ?其?餈質馱蝑????漱閮??敺?????
    ??蝺?摰?????湔瘜?蝪∪????頛??
    """
    def __init__(self):
        self._lock = Lock()
        self.position: int = 0
        self.open_orders: Dict[str, Dict[str, Any]] = {}  # order_id -> info
        self.last_signal_ts: float = 0.0

    # 霈??蝺?摰嚗?
    def add_position(self, qty: int) -> None:
        with self._lock:
            self.position += int(qty)
            if self.position < 0:
                self.position = 0

    def reduce_position(self, qty: int) -> None:
        with self._lock:
            self.position -= int(qty)
            if self.position < 0:
                self.position = 0

    # open_orders ??
    def add_order(self, order_id: str, info: Dict[str, Any]) -> None:
        with self._lock:
            self.open_orders[order_id] = info

    def remove_order(self, order_id: str) -> None:
        with self._lock:
            if order_id in self.open_orders:
                del self.open_orders[order_id]

    def update_order(self, order_id: str, info_updates: Dict[str, Any]) -> None:
        with self._lock:
            if order_id in self.open_orders:
                self.open_orders[order_id].update(info_updates)
            else:
                self.open_orders[order_id] = dict(info_updates)

    # last_signal_ts ??
    def set_last_signal_ts(self, ts: float) -> None:
        with self._lock:
            self.last_signal_ts = float(ts)

    # ???嗅???翰?改??憛?鋆踝?
    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "position": int(self.position),
                "open_orders": dict(self.open_orders),
                "last_signal_ts": float(self.last_signal_ts),
            }

    # ?蔭???撠?雿輻嚗?
    def reset(self) -> None:
        with self._lock:
            self.position = 0
            self.open_orders.clear()
            self.last_signal_ts = 0.0

    def __repr__(self) -> str:
        s = self.snapshot()
        return f"StrategyState(position={s['position']}, open_orders={len(s['open_orders'])}, last_signal_ts={s['last_signal_ts']})"
