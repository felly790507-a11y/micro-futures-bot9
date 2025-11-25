# trading_mvp.py
"""
Tick-first trading MVP (debug-ready, BidAsk-integrated, orderbook de-dup & throttle)
- 每 AGG_SIZE 筆 tick 合成一根 K-bar，並寫入 kbars.csv
- 預設 SIMULATE_TRADES = True（不送真單），會把模擬交易寫入 trades_sim.csv
- 會把五檔 orderbook 快照寫入 orderbook.csv（若 API 提供 BidAsk）
- 已包含固定 round-trip 手續費 FEE_PER_ROUNDTRIP = 40 元
- 包含 debug 選項：VERBOSE、TEST_WRITE、TEST_SIMULATE_TICKS（短期測試用）
- on_orderbook_callback 支援多種呼叫簽名、使用 q.datetime 作為時間戳、並做去重與節流
- 請放置 config.json（含 api_key, secret_key）
"""

import csv
import json
import time
import threading
import statistics
import random
from collections import deque, namedtuple
from pathlib import Path

# 若沒有 shioaji 環境，程式仍能在 TEST 模式下執行合成/寫檔測試
try:
    import shioaji as sj
    SHIOAJI_AVAILABLE = True
except Exception:
    sj = None
    SHIOAJI_AVAILABLE = False

# -------------------------
# 設定（可調）
# -------------------------
CONFIG_FILE = "config.json"
SIMULATION = True        # Shioaji simulation mode
VERBOSE = True           # True 顯示詳細 debug 日誌（測試時建議 True）
SIMULATE_TRADES = True   # True: 模擬進出（不送真單）
AGG_SIZE = 3             # 每 AGG_SIZE 筆 tick 合成一根 K-bar
TICK_UNIT = 0.5

REQUIRED_RISE_BARS = 3
VOLUME_MULTIPLIER = 1.2
BOOK_DEPTH_MULTIPLIER = 1.2

ORDER_TIMEOUT = 0.8
ORDER_QTY = 1

HIST_VOL_WINDOW = 50
LOG_PREFIX = "[MVP]"

# Debug / test helpers
TEST_WRITE = True            # 啟動時寫入一行測試到 trades_sim.csv / orderbook.csv（驗證權限）
TEST_SIMULATE_TICKS = False  # 啟動時模擬幾筆 tick 以快速產生 kbars（測試用）
TEST_SIM_TICKS_COUNT = 30

# Orderbook write throttle (seconds) and dedupe
ORDERBOOK_WRITE_THROTTLE = 0.2  # 最小寫檔間隔（秒）
# -------------------------
# 手續費（round-trip）
# -------------------------
FEE_PER_ROUNDTRIP = 40.0

# -------------------------
# CSV 設定
# -------------------------
KBAR_CSV = Path("kbars.csv")
KBAR_CSV_HEADER = ["start_time", "end_time", "open", "high", "low", "close", "volume"]
TRADES_CSV = Path("trades_sim.csv")
TRADES_HEADER = ["entry_time", "exit_time", "entry_price", "exit_price", "size", "pnl_before_fee", "fee", "pnl_after_fee"]

ORDERBOOK_CSV = Path("orderbook.csv")
ORDERBOOK_HEADER = [
    "ts", "side",
    "p1", "q1", "p2", "q2", "p3", "q3", "p4", "q4", "p5", "q5",
    "total_vol", "first_price", "first_vol"
]

# -------------------------
# 資料結構與全域狀態
# -------------------------
KBar = namedtuple("KBar", ["open", "high", "low", "close", "volume", "start_time", "end_time"])

tick_buffer = []
tick_seen = deque(maxlen=10000)
tick_seen_set = set()
kbar_history = deque(maxlen=2000)
vol_history = deque(maxlen=HIST_VOL_WINDOW)
orderbook_snapshot = None

rise_count = 0
fall_count = 0
last_kbar_close = None
lock = threading.Lock()
stop_event = threading.Event()

# 模擬交易狀態
sim_position = 0
sim_entry_price = None
sim_entry_time = None
sim_trades = []  # list of dicts for CSV and summary
sim_equity_curve = []

# -------------------------
# 初始化 CSV 檔（若不存在則建立）
# -------------------------
try:
    if not KBAR_CSV.exists():
        with KBAR_CSV.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(KBAR_CSV_HEADER)
except Exception:
    pass

try:
    if not TRADES_CSV.exists():
        with TRADES_CSV.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(TRADES_HEADER)
except Exception:
    pass

try:
    if not ORDERBOOK_CSV.exists():
        with ORDERBOOK_CSV.open("w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(ORDERBOOK_HEADER)
except Exception:
    pass

# -------------------------
# 讀取設定並登入（若可用）
# -------------------------
api = None
contract = None
if SHIOAJI_AVAILABLE:
    try:
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        api = sj.Shioaji(simulation=SIMULATION)
        api.login(api_key=cfg["api_key"], secret_key=cfg["secret_key"])
        print(f"{LOG_PREFIX} 已登入 Shioaji (simulation={SIMULATION})")
        # 選近月微型台合約（視環境而定）
        try:
            contract = min(
                [x for x in api.Contracts.Futures.TMF if x.code[-2:] not in ["R1", "R2"]],
                key=lambda x: x.delivery_date
            )
            print(f"{LOG_PREFIX} 選擇合約: {contract.code}")
        except Exception:
            contract = None
    except Exception as e:
        print(f"{LOG_PREFIX} Shioaji login failed or config missing: {e}")
        api = None
else:
    if VERBOSE:
        print(f"{LOG_PREFIX} shioaji not available, running in local/test mode")

# -------------------------
# 工具函式
# -------------------------
def make_kbar_from_ticks(ticks):
    prices = [t["price"] for t in ticks]
    vols = [t["volume"] for t in ticks]
    return KBar(
        open=prices[0],
        high=max(prices),
        low=min(prices),
        close=prices[-1],
        volume=sum(vols),
        start_time=ticks[0]["time"],
        end_time=ticks[-1]["time"]
    )

def append_kbar_to_csv(k):
    try:
        with KBAR_CSV.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                int(k.start_time), int(k.end_time),
                round(k.open,2), round(k.high,2), round(k.low,2), round(k.close,2),
                int(k.volume)
            ])
        if VERBOSE:
            print(f"{LOG_PREFIX} wrote kbar {int(k.start_time)} -> {int(k.end_time)} O{round(k.open,2)} C{round(k.close,2)} V{int(k.volume)}")
    except Exception as e:
        if VERBOSE:
            print(f"{LOG_PREFIX} append_kbar_to_csv failed: {e}")

def append_trade_to_csv(tr):
    try:
        with TRADES_CSV.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                int(tr["entry_time"]), int(tr["exit_time"]),
                round(tr["entry_price"],2), round(tr["exit_price"],2),
                int(tr["size"]), round(tr["pnl_before_fee"],2),
                round(tr["fee"],2), round(tr["pnl_after_fee"],2)
            ])
        if VERBOSE:
            print(f"{LOG_PREFIX} trade written entry={int(tr['entry_time'])} exit={int(tr['exit_time'])} pnl_after_fee={round(tr['pnl_after_fee'],2)}")
    except Exception as e:
        if VERBOSE:
            print(f"{LOG_PREFIX} append_trade_to_csv failed: {e}")

def write_orderbook_snapshot(side, arr, ts=None, total_vol=None, first_price=None, first_vol=None):
    """
    side: 'bids' or 'asks'
    arr: list of (price, qty) tuples (最多 5 檔)
    ts: optional unix timestamp (int)，預設使用 current time
    total_vol: optional total vol (bid_total_vol / ask_total_vol)
    first_price: optional first derived price
    first_vol: optional first derived vol
    """
    if ts is None:
        ts = int(time.time())
    row = [int(ts), side]
    for i in range(5):
        if i < len(arr):
            p, q = arr[i]
            try:
                row += [round(float(p), 2), int(q)]
            except Exception:
                row += ["", ""]
        else:
            row += ["", ""]
    # append metadata columns
    row += [int(total_vol) if total_vol is not None else "", round(float(first_price), 2) if first_price is not None else "", int(first_vol) if first_vol is not None else ""]
    try:
        with ORDERBOOK_CSV.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)
        if VERBOSE:
            print(f"{LOG_PREFIX} orderbook snapshot written ts={ts} side={side} total_vol={total_vol}")
    except Exception as e:
        if VERBOSE:
            print(f"{LOG_PREFIX} write_orderbook_snapshot failed: {e}")

def avg_vol():
    return statistics.mean(vol_history) if vol_history else 0

def orderbook_cum_opposite_volume(side):
    if not orderbook_snapshot:
        return 0
    arr = orderbook_snapshot.get("asks" if side == "buy" else "bids", [])
    return sum(q for p, q in arr[:5])

def estimate_aggressive_price(side, tick_offset=0):
    if not orderbook_snapshot:
        return None
    try:
        if side == 'buy':
            best_ask = orderbook_snapshot["asks"][0][0]
            return round(best_ask + tick_offset * TICK_UNIT, 2)
        else:
            best_bid = orderbook_snapshot["bids"][0][0]
            return round(best_bid - tick_offset * TICK_UNIT, 2)
    except Exception:
        return None

# -------------------------
# 模擬交易：進場 / 平倉（簡單）
# -------------------------
def sim_enter(size, price, tstamp):
    global sim_position, sim_entry_price, sim_entry_time
    if sim_position != 0:
        return
    sim_position = size
    sim_entry_price = price
    sim_entry_time = tstamp
    if VERBOSE:
        print(f"{LOG_PREFIX} [SIM] Enter {size} @ {price} time={time.strftime('%H:%M:%S', time.localtime(tstamp))}")

def sim_exit(price, tstamp):
    global sim_position, sim_entry_price, sim_entry_time, sim_trades
    if sim_position == 0 or sim_entry_price is None:
        return
    size = sim_position
    pnl_before_fee = (price - sim_entry_price) * size  # 假設每點價值為 1
    fee = FEE_PER_ROUNDTRIP
    pnl_after_fee = pnl_before_fee - fee
    trade = {
        "entry_time": sim_entry_time,
        "exit_time": tstamp,
        "entry_price": sim_entry_price,
        "exit_price": price,
        "size": size,
        "pnl_before_fee": pnl_before_fee,
        "fee": fee,
        "pnl_after_fee": pnl_after_fee
    }
    sim_trades.append(trade)
    append_trade_to_csv(trade)
    # 更新 equity curve
    last_equity = sim_equity_curve[-1] if sim_equity_curve else 0.0
    sim_equity_curve.append(last_equity + pnl_after_fee)
    if VERBOSE:
        print(f"{LOG_PREFIX} [SIM] Exit {size} @ {price} pnl_after_fee={pnl_after_fee} (before fee {pnl_before_fee})")
    # reset
    sim_position = 0
    sim_entry_price = None
    sim_entry_time = None

# -------------------------
# 策略核心（含反向訊號平倉）
# -------------------------
def update_vol_history(kbar):
    vol_history.append(kbar.volume)

def on_new_kbar(k):
    global rise_count, fall_count, last_kbar_close
    if VERBOSE:
        print(f"{LOG_PREFIX} on_new_kbar -> O{round(k.open,2)} C{round(k.close,2)} V{int(k.volume)}")
    # append & persist
    try:
        with lock:
            kbar_history.append(k)
        append_kbar_to_csv(k)
    except Exception as e:
        if VERBOSE:
            print(f"{LOG_PREFIX} append kbar failed: {e}")

    # update vol history
    try:
        update_vol_history(k)
    except Exception:
        pass

    # decision logic: rise_count, fall_count, entry, reverse-exit
    try:
        is_up = k.close > k.open
        is_down = k.close < k.open
        vol_ok = (avg_vol() == 0) or (k.volume >= avg_vol() * VOLUME_MULTIPLIER)

        # update counters
        if is_up and vol_ok:
            rise_count += 1
            fall_count = 0
        elif is_down and vol_ok:
            fall_count += 1
            rise_count = 0
        else:
            # neutral or low volume: reset counts
            rise_count = 0
            fall_count = 0

        last_kbar_close = k.close

        if VERBOSE or rise_count >= REQUIRED_RISE_BARS or fall_count >= 1:
            print(f"{LOG_PREFIX} K-bar C{round(k.close,2)} V{int(k.volume)} rise={rise_count} fall={fall_count}")

        # entry condition
        if rise_count >= REQUIRED_RISE_BARS:
            side = 'buy'
            cum = orderbook_cum_opposite_volume(side)
            if cum >= ORDER_QTY * BOOK_DEPTH_MULTIPLIER:
                price = estimate_aggressive_price(side) or k.close
                if SIMULATE_TRADES:
                    sim_enter(ORDER_QTY, price, k.end_time)
                else:
                    # In live mode you'd place an order here; currently we avoid auto live orders
                    print(f"{LOG_PREFIX} (LIVE) would place entry order price={price}")
            else:
                if VERBOSE:
                    print(f"{LOG_PREFIX} 五檔深度不足 cum={cum}")

        # reverse-signal exit: if holding and current kbar is down (and vol_ok), exit
        if SIMULATE_TRADES and sim_position != 0:
            # default: single down kbar with volume condition triggers exit
            if is_down and vol_ok:
                sim_exit(k.close, k.end_time)
                # reset counters to avoid immediate re-entry
                rise_count = 0
                fall_count = 0

    except Exception as e:
        if VERBOSE:
            print(f"{LOG_PREFIX} on_new_kbar error: {e}")

# -------------------------
# Tick 合成
# -------------------------
def on_tick_received(tick):
    with lock:
        tick_buffer.append(tick)
        if VERBOSE:
            print(f"{LOG_PREFIX} tick {tick['price']} v{tick['volume']}")
        if len(tick_buffer) >= AGG_SIZE:
            k = make_kbar_from_ticks(tick_buffer[:AGG_SIZE])
            del tick_buffer[:AGG_SIZE]
    if 'k' in locals():
        on_new_kbar(k)

# -------------------------
# filtered_tick_handler（解析 Solace Tick 或 API tick）
# -------------------------
def filtered_tick_handler(exchange, tick):
    try:
        code = getattr(tick, "code", None)
        if contract and code is not None and code != contract.code:
            return
        price = getattr(tick, "close", None)
        vol = getattr(tick, "volume", None) or 0
        ts_dt = getattr(tick, "datetime", None)
        tid = getattr(tick, "tick_type", None) or getattr(tick, "seq", None) or getattr(tick, "id", None)
        if price is None:
            return
        price = float(price)
        vol = int(vol)
        ts = ts_dt.timestamp() if ts_dt is not None else time.time()
        key = ("id", str(tid)) if tid is not None else ("tpv", round(ts, 3), round(price, 4), int(vol))
        if key in tick_seen_set:
            return
        tick_seen.append(key); tick_seen_set.add(key)
        if len(tick_seen) > tick_seen.maxlen:
            try:
                old = tick_seen.popleft(); tick_seen_set.discard(old)
            except Exception:
                tick_seen.clear(); tick_seen_set.clear()
        internal_tick = {"price": price, "volume": vol, "time": ts, "id": tid}
        on_tick_received(internal_tick)
    except Exception as e:
        if VERBOSE:
            print(f"{LOG_PREFIX} filtered_tick_handler parse error: {e}")

# -------------------------
# Orderbook 回呼（支援 BidAsk 解析、節流與去重）
# -------------------------
def on_orderbook_callback(*args, **kwargs):
    """
    Compatible callback: accepts (exchange, quote) or (topic, quote) or (quote,) or kwargs.
    Extracts bid_price/bid_volume and ask_price/ask_volume if present.
    Uses q.datetime as ts when available, applies throttle and dedupe to avoid excessive writes.
    """
    global orderbook_snapshot
    try:
        # extract quote-like object (usually last positional arg)
        q = None
        if args:
            q = args[-1]
        elif "quote" in kwargs:
            q = kwargs["quote"]
        else:
            q = kwargs or None

        if q is None:
            if VERBOSE:
                print(f"{LOG_PREFIX} on_orderbook_callback: no quote found in args/kwargs")
            return

        # throttle: limit writes to at most once per ORDERBOOK_WRITE_THROTTLE seconds
        last_write = getattr(on_orderbook_callback, "_last_write", 0.0)
        now = time.time()
        if now - last_write < ORDERBOOK_WRITE_THROTTLE:
            # still update snapshot in memory but skip file write/dedupe check
            try:
                # attempt to parse into snapshot for strategy use
                bids_tmp, asks_tmp = [], []
                if hasattr(q, "bid_price") and hasattr(q, "bid_volume"):
                    for p, qv in zip(q.bid_price, q.bid_volume):
                        bids_tmp.append((float(str(p)), int(qv)))
                    for p, qv in zip(q.ask_price, q.ask_volume):
                        asks_tmp.append((float(str(p)), int(qv)))
                else:
                    bids_attr = getattr(q, "bids", None)
                    asks_attr = getattr(q, "asks", None)
                    def norm_side(arr):
                        out = []
                        if not arr:
                            return out
                        for it in arr[:5]:
                            if isinstance(it, (list, tuple)) and len(it) >= 2:
                                p, qv = it[0], it[1]
                            else:
                                p = getattr(it, "price", None) or (it.get("price") if isinstance(it, dict) else None)
                                qv = getattr(it, "qty", None) or getattr(it, "volume", None) or (it.get("qty") if isinstance(it, dict) else None)
                            try:
                                out.append((float(p), int(qv or 0)))
                            except Exception:
                                continue
                        return out
                    bids_tmp = norm_side(bids_attr) if bids_attr is not None else []
                    asks_tmp = norm_side(asks_attr) if asks_attr is not None else []
                orderbook_snapshot = {"bids": bids_tmp[:5], "asks": asks_tmp[:5]}
            except Exception:
                pass
            return

        if VERBOSE:
            try:
                print(f"{LOG_PREFIX} raw orderbook q: {repr(q)[:1000]}")
            except Exception:
                pass

        bids = []
        asks = []
        total_bid_vol = None
        total_ask_vol = None
        first_bid_price = None
        first_bid_vol = None
        first_ask_price = None
        first_ask_vol = None

        # Case A: BidAsk-like object with bid_price/bid_volume attributes
        if hasattr(q, "bid_price") and hasattr(q, "bid_volume") and hasattr(q, "ask_price") and hasattr(q, "ask_volume"):
            try:
                for p, qv in zip(q.bid_price, q.bid_volume):
                    bids.append((float(str(p)), int(qv)))
                for p, qv in zip(q.ask_price, q.ask_volume):
                    asks.append((float(str(p)), int(qv)))
            except Exception:
                bids = [(float(str(p)), int(qv)) for p, qv in zip(q.bid_price, q.bid_volume)]
                asks = [(float(str(p)), int(qv)) for p, qv in zip(q.ask_price, q.ask_volume)]
            total_bid_vol = getattr(q, "bid_total_vol", None)
            total_ask_vol = getattr(q, "ask_total_vol", None)
            first_bid_price = getattr(q, "first_derived_bid_price", None)
            first_bid_vol = getattr(q, "first_derived_bid_vol", None)
            first_ask_price = getattr(q, "first_derived_ask_price", None)
            first_ask_vol = getattr(q, "first_derived_ask_vol", None)
        else:
            # Case B: dict-like or other structure
            bids_raw = None
            asks_raw = None
            if isinstance(q, dict):
                bids_raw = q.get("bid_price") or q.get("bids") or q.get("bid")
                asks_raw = q.get("ask_price") or q.get("asks") or q.get("ask")
                bids_vol_raw = q.get("bid_volume") or q.get("bid_volume_list") or q.get("bids_vol")
                asks_vol_raw = q.get("ask_volume") or q.get("ask_volume_list") or q.get("asks_vol")
                if bids_raw and bids_vol_raw:
                    for p, qv in zip(bids_raw, bids_vol_raw):
                        bids.append((float(p), int(qv)))
                if asks_raw and asks_vol_raw:
                    for p, qv in zip(asks_raw, asks_vol_raw):
                        asks.append((float(p), int(qv)))
                total_bid_vol = q.get("bid_total_vol") or q.get("bid_total")
                total_ask_vol = q.get("ask_total_vol") or q.get("ask_total")
            else:
                bids_attr = getattr(q, "bids", None)
                asks_attr = getattr(q, "asks", None)
                def norm_side(arr):
                    out = []
                    if not arr:
                        return out
                    for it in arr[:5]:
                        if isinstance(it, (list, tuple)) and len(it) >= 2:
                            p, qv = it[0], it[1]
                        else:
                            p = getattr(it, "price", None) or (it.get("price") if isinstance(it, dict) else None)
                            qv = getattr(it, "qty", None) or getattr(it, "volume", None) or (it.get("qty") if isinstance(it, dict) else None)
                        try:
                            out.append((float(p), int(qv or 0)))
                        except Exception:
                            continue
                    return out
                bids = norm_side(bids_attr) if bids_attr is not None else []
                asks = norm_side(asks_attr) if asks_attr is not None else []
                total_bid_vol = getattr(q, "bid_total_vol", None) or (q.get("bid_total_vol") if isinstance(q, dict) else None)
                total_ask_vol = getattr(q, "ask_total_vol", None) or (q.get("ask_total_vol") if isinstance(q, dict) else None)

        bids = bids[:5]
        asks = asks[:5]

        # dedupe: skip write if identical to last snapshot
        cur_snapshot = (tuple(bids), tuple(asks))
        last_snapshot = getattr(on_orderbook_callback, "_last_snapshot", None)
        if last_snapshot == cur_snapshot:
            # still update in-memory snapshot for strategy use
            orderbook_snapshot = {"bids": bids, "asks": asks}
            # update last_write timestamp to avoid immediate subsequent writes if needed
            on_orderbook_callback._last_write = time.time()
            return

        # determine timestamp: prefer q.datetime if available
        ts_now = None
        try:
            qdt = getattr(q, "datetime", None)
            if qdt is not None:
                # q.datetime may be a datetime object
                ts_now = int(qdt.timestamp())
        except Exception:
            ts_now = None
        if ts_now is None:
            ts_now = int(time.time())

        # write both sides
        try:
            if bids:
                write_orderbook_snapshot("bids", bids, ts=ts_now, total_vol=total_bid_vol, first_price=first_bid_price, first_vol=first_bid_vol)
            if asks:
                write_orderbook_snapshot("asks", asks, ts=ts_now, total_vol=total_ask_vol, first_price=first_ask_price, first_vol=first_ask_vol)
            # update last write and last snapshot
            on_orderbook_callback._last_write = time.time()
            on_orderbook_callback._last_snapshot = cur_snapshot
            # update in-memory snapshot
            orderbook_snapshot = {"bids": bids, "asks": asks}
        except Exception as e:
            if VERBOSE:
                print(f"{LOG_PREFIX} failed to write orderbook snapshot: {e}")

    except Exception as e:
        if VERBOSE:
            print(f"{LOG_PREFIX} orderbook parse failed: {e}")

# -------------------------
# 事件回呼
# -------------------------
def event_cb(*args, **kwargs):
    if VERBOSE:
        print(f"{LOG_PREFIX} EVENT: {args} {kwargs}")

def session_down_cb(*args, **kwargs):
    print(f"{LOG_PREFIX} SESSION DOWN")

# -------------------------
# 註冊回呼與訂閱（若 API 可用）
# -------------------------
if api:
    try:
        api.quote.set_on_tick_fop_v1_callback(filtered_tick_handler)
        if VERBOSE:
            print(f"{LOG_PREFIX} tick callback registered")
    except Exception as e:
        print(f"{LOG_PREFIX} 註冊 tick 回呼失敗: {e}")

    try:
        if hasattr(api.quote, "on_event"):
            api.quote.on_event(event_cb)
        if hasattr(api.quote, "set_session_down_callback"):
            api.quote.set_session_down_callback(session_down_cb)
    except Exception:
        pass

    # 訂閱合約（tick）
    try:
        if hasattr(api.quote, "subscribe") and contract:
            api.quote.subscribe(contract)
        else:
            try:
                api.quote.ticks(contract)
            except Exception:
                pass
        if VERBOSE:
            print(f"{LOG_PREFIX} subscribed to ticks for {contract.code if contract else 'N/A'}")
    except Exception as e:
        print(f"{LOG_PREFIX} subscribe failed: {e}")

    # 註冊 BidAsk / orderbook 回呼（若 API 支援）
    try:
        if hasattr(api.quote, "set_on_bidask_fop_v1_callback"):
            api.quote.set_on_bidask_fop_v1_callback(on_orderbook_callback)
        elif hasattr(api.quote, "on_bidask_fop_v1_callback"):
            api.quote.on_bidask_fop_v1_callback(on_orderbook_callback)
        elif hasattr(api.quote, "set_on_bidask_stk_v1_callback"):
            api.quote.set_on_bidask_stk_v1_callback(on_orderbook_callback)
        else:
            # fallback: try subscribing with QuoteType.BidAsk if API supports subscribe signature
            try:
                if hasattr(sj.constant, "QuoteType") and contract:
                    api.quote.subscribe(contract, quote_type=sj.constant.QuoteType.BidAsk, version=sj.constant.QuoteVersion.v1)
            except Exception:
                pass
        if VERBOSE:
            print(f"{LOG_PREFIX} attempted to register orderbook callback")
    except Exception:
        if VERBOSE:
            print(f"{LOG_PREFIX} orderbook callback registration failed")

# -------------------------
# Heartbeat 與主迴圈
# -------------------------
def heartbeat():
    while not stop_event.is_set():
        if VERBOSE:
            print(f"{LOG_PREFIX} heartbeat kbars={len(kbar_history)} ticks_buf={len(tick_buffer)} sim_pos={sim_position} orderbook={bool(orderbook_snapshot)}")
        time.sleep(5)

hb = threading.Thread(target=heartbeat, daemon=True)
hb.start()

# -------------------------
# 測試寫檔（驗證權限）與模擬 ticks（短期）
# -------------------------
def do_test_write():
    try:
        # trades_sim test row
        with TRADES_CSV.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([int(time.time()), int(time.time()), 0, 0, 0, 0, 0, 0])
        # orderbook test row
        with ORDERBOOK_CSV.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([int(time.time()), "bids", "", "", "", "", "", "", "", "", "", "", ""])
        if VERBOSE:
            print(f"{LOG_PREFIX} test rows written to trades_sim.csv and orderbook.csv")
    except Exception as e:
        print(f"{LOG_PREFIX} test write failed: {e}")

def simulate_local_ticks(n=30, base_price=26850):
    """短期模擬 tick 以快速產生 kbars（僅測試用）"""
    for i in range(n):
        price = base_price + random.choice([-1, 0, 1]) * 0.5 + random.random() * 0.1
        vol = random.randint(1, 5)
        ts = time.time()
        internal_tick = {"price": round(price, 2), "volume": vol, "time": ts, "id": f"sim{i}"}
        on_tick_received(internal_tick)
        time.sleep(0.01)

# -------------------------
# 主迴圈
# -------------------------
try:
    # 印出工作目錄以便確認檔案位置
    try:
        from pathlib import Path as _P
        print(f"{LOG_PREFIX} cwd: {_P.cwd()}")
    except Exception:
        pass

    # 測試寫檔（若啟用）
    if TEST_WRITE:
        do_test_write()

    # 短期模擬 ticks（若啟用）
    if TEST_SIMULATE_TICKS:
        simulate_local_ticks(TEST_SIM_TICKS_COUNT)

    print(f"{LOG_PREFIX} 啟動完成（SIMULATE_TRADES={SIMULATE_TRADES} VERBOSE={VERBOSE}），按 Ctrl+C 停止")
    while not stop_event.is_set():
        time.sleep(1)
except KeyboardInterrupt:
    stop_event.set()
finally:
    # 若模擬仍有未平倉部位，於結束時以最後 kbar close 平倉（若有）
    try:
        if SIMULATE_TRADES and sim_position != 0 and kbar_history:
            last_price = kbar_history[-1].close
            last_time = kbar_history[-1].end_time
            sim_exit(last_price, last_time)
    except Exception:
        pass

    # 計算模擬績效摘要並印出
    try:
        total_pnl = sum(t["pnl_after_fee"] for t in sim_trades) if sim_trades else 0.0
        num_roundtrips = len(sim_trades)
        wins = sum(1 for t in sim_trades if t["pnl_after_fee"] > 0)
        win_rate = (wins / num_roundtrips) if num_roundtrips > 0 else 0.0
        # max drawdown from equity curve
        if sim_equity_curve:
            peak = -float("inf")
            max_dd = 0.0
            for v in sim_equity_curve:
                if v > peak:
                    peak = v
                dd = peak - v
                if dd > max_dd:
                    max_dd = dd
        else:
            max_dd = 0.0
        print(f"{LOG_PREFIX} 模擬交易總結: roundtrips={num_roundtrips} net_pnl={total_pnl:.2f} wins={wins} win_rate={win_rate:.2%} max_drawdown={max_dd:.2f}")
    except Exception:
        pass

    try:
        if api and hasattr(api.quote, "unsubscribe") and contract:
            api.quote.unsubscribe(contract)
    except Exception:
        pass
    try:
        if api:
            api.logout()
    except Exception:
        pass
    print(f"{LOG_PREFIX} 程式已結束")
