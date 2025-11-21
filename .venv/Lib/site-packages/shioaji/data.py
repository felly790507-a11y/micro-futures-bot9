import typing
import datetime
from collections import abc

from pydantic import validator
from shioaji.base import BaseModel
from shioaji.constant import ChangeType, TickType, Exchange


class Ticks(BaseModel):
    ts: typing.List[int]
    close: typing.List[float]
    volume: typing.List[int]
    bid_price: typing.List[float]
    bid_volume: typing.List[int]
    ask_price: typing.List[float]
    ask_volume: typing.List[int]
    tick_type: typing.List[int]


class Snapshot(BaseModel):
    ts: int
    code: str
    exchange: str
    open: float
    high: float
    low: float
    close: float
    tick_type: TickType
    change_price: float
    change_rate: float
    change_type: ChangeType
    average_price: float
    volume: int
    total_volume: int
    amount: int
    total_amount: int
    yesterday_volume: float
    buy_price: float
    buy_volume: float
    sell_price: float
    sell_volume: int
    volume_ratio: float


class CreditEnquire(BaseModel):
    update_time: str = ""
    system: str = ""
    stock_id: str = ""
    margin_unit: int = 0
    short_unit: int = 0


class ShortStockSource(BaseModel):
    code: str
    short_stock_source: int = 0
    ts: int


class Kbars(BaseModel):
    ts: typing.List[int]
    Open: typing.List[float]
    High: typing.List[float]
    Low: typing.List[float]
    Close: typing.List[float]
    Volume: typing.List[int]
    Amount: typing.List[float]


class DailyQuotes(BaseModel):
    Date: typing.List[datetime.date]
    Code: typing.List[str]
    Open: typing.List[float]
    High: typing.List[float]
    Low: typing.List[float]
    Close: typing.List[float]
    Volume: typing.List[int]
    Transaction: typing.List[int]
    Amount: typing.List[int]


class ScannerItem(BaseModel):
    date: str
    code: str
    name: str
    ts: int
    open: float
    high: float
    low: float
    close: float
    price_range: float
    tick_type: int
    change_price: float
    change_type: int
    average_price: float
    volume: int
    total_volume: int
    amount: int
    total_amount: int
    yesterday_volume: int
    volume_ratio: float
    buy_price: float
    buy_volume: int
    sell_price: float
    sell_volume: int
    bid_orders: int
    bid_volumes: int
    ask_orders: int
    ask_volumes: int
    rank_value: typing.Union[float, int]


class UsageStatus(BaseModel):
    connections: int = 0
    bytes: int = 0
    limit_bytes: int = 0
    remaining_bytes: int = 0


class Punish(BaseModel):
    code: typing.List[str]
    start_date: typing.List[typing.Optional[datetime.date]]
    end_date: typing.List[typing.Optional[datetime.date]]
    updated_at: typing.List[typing.Optional[datetime.datetime]]
    interval: typing.List[str]
    unit_limit: typing.List[typing.Optional[float]]
    total_limit: typing.List[typing.Optional[float]]
    description: typing.List[str]
    announced_date: typing.List[typing.Optional[datetime.date]]


class Notice(BaseModel):
    code: typing.List[str]
    updated_at: typing.List[typing.Optional[datetime.datetime]]
    close: typing.List[typing.Optional[float]]
    reason: typing.List[str]
    announced_date: typing.List[typing.Optional[datetime.date]]