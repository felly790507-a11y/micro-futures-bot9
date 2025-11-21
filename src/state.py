# src/state.py
class StrategyState:
    def __init__(self):
        self.position = 0
        self.open_orders = {}  # order_id -> info
        self.last_signal_ts = 0.0

    def add_position(self, qty):
        self.position += qty

    def reduce_position(self, qty):
        self.position -= qty
        if self.position < 0:
            self.position = 0
