# tests/test_kbar.py
from src.signal import KBarAggregator
from src.data import Tick

def test_kbar_3ticks():
    agg = KBarAggregator(n=3)
    ticks = [Tick(0,100,1,"B"), Tick(1,101,1,"B"), Tick(2,102,1,"B")]
    k = agg.add_tick(ticks[0]); assert k is None
    k = agg.add_tick(ticks[1]); assert k is None
    k = agg.add_tick(ticks[2]); assert k is not None
    assert k.open == 100 and k.close == 102 and k.high == 102 and k.low == 100
