import datetime
import typing
from shioaji.account import Account
from shioaji.base import BaseModel
from shioaji.constant import Action, Currency, StockOrderCond, TradeType
from shioaji.contracts import FetchStatus


class LazyModel(BaseModel):
    status: FetchStatus = FetchStatus.Unfetch

    def lazy_setter(self, **kwargs):
        super().lazy_setter(status=FetchStatus.Fetched, **kwargs)


class Position(BaseModel):
    id: int
    code: str
    direction: Action
    quantity: int
    price: float
    last_price: float
    pnl: float


class StockPosition(Position):
    yd_quantity: int
    cond: StockOrderCond = StockOrderCond.Cash
    margin_purchase_amount: int
    collateral: int
    short_sale_margin: int
    interest: int


class FuturePosition(Position):
    pass


class PositionDetail(BaseModel):
    date: str
    code: str
    quantity: int
    price: float = 0
    last_price: float
    dseq: str
    direction: Action
    pnl: float
    currency: Currency
    fee: typing.Union[float, int] = 0


class StockPositionDetail(PositionDetail):
    cond: StockOrderCond = StockOrderCond.Cash
    ex_dividends: int = 0
    interest: int = 0
    margintrading_amt: int = 0
    collateral: int = 0


class FuturePositionDetail(PositionDetail):
    entry_quantity: int


class ProfitLoss(BaseModel):
    id: int
    code: str
    quantity: int
    pnl: float
    date: str


class FutureProfitLoss(ProfitLoss):
    direction: Action
    entry_price: float
    cover_price: float
    tax: int
    fee: int


class StockProfitLoss(ProfitLoss):
    dseq: str
    price: float
    pr_ratio: float = 0.0  # [stock only]
    cond: StockOrderCond = StockOrderCond.Cash
    seqno: str


class Settlement(LazyModel):
    t_money: float
    t1_money: float
    t2_money: float
    t_day: str
    t1_day: str
    t2_day: str


class SettlementV1(BaseModel):
    date: datetime.date
    amount: float
    T: int


class AccountBalance(LazyModel):
    acc_balance: float
    date: str
    errmsg: str


class ProfitLossDetail(BaseModel):
    date: str
    code: str
    quantity: int
    dseq: str
    fee: int
    tax: int
    currency: str


class FutureProfitDetail(ProfitLossDetail):
    direction: Action
    entry_date: str
    entry_price: float
    cover_price: float
    pnl: int = 0


class StockProfitDetail(ProfitLossDetail):
    price: float
    cost: int
    rep_margintrading_amt: int
    rep_collateral: int
    rep_margin: int
    shortselling_fee: int
    ex_dividend_amt: int
    interest: int
    trade_type: TradeType = TradeType.Common
    cond: StockOrderCond = StockOrderCond.Cash


class ProfitLossSummary(BaseModel):
    code: str
    quantity: int
    entry_price: float
    cover_price: float
    pnl: float
    currency: str


class FutureProfitLossSummary(ProfitLossSummary):
    direction: Action
    tax: int
    fee: int


class StockProfitLossSummary(ProfitLossSummary):
    entry_cost: int
    cover_cost: int
    buy_cost: int
    sell_cost: int
    pr_ratio: float
    cond: StockOrderCond = StockOrderCond.Cash


class ProfitLossTotal(BaseModel):
    entry_amount: int = 0
    cover_amount: int = 0
    quantity: int = 0
    buy_cost: int = 0
    sell_cost: int = 0
    pnl: float = 0.0
    pr_ratio: float = 0.0


class ProfitLossSummaryTotal(LazyModel):
    profitloss_summary: typing.List[
        typing.Union[StockProfitLossSummary, FutureProfitLossSummary]
    ]
    total: ProfitLossTotal


class Margin(LazyModel):
    yesterday_balance: float  # 前日餘額
    today_balance: float  # 本日餘額
    deposit_withdrawal: float  # 存提
    fee: float  # 手續費
    tax: float  # 期交稅
    initial_margin: float  # 原始保證金
    maintenance_margin: float  # 維持保證金
    margin_call: float  # 追繳保證金
    risk_indicator: float  # 風險指標
    royalty_revenue_expenditure: float  # 權利金收入與支出
    equity: float  # 權益數
    equity_amount: float  # 權益總值
    option_openbuy_market_value: float  # 未沖銷買方選擇權市值
    option_opensell_market_value: float  # 未沖銷賣方選擇權市值
    option_open_position: float  # 參考未平倉選擇權損益
    option_settle_profitloss: float  # 參考選擇權平倉損益
    future_open_position: float  # 未沖銷期貨浮動損益
    today_future_open_position: float  # 參考當日未沖銷期貨浮動損益
    future_settle_profitloss: float  # 期貨平倉損益
    available_margin: float  # 可動用(出金)保證金
    plus_margin: float  # 依「加收保證金指標」所加收之保證金
    plus_margin_indicator: float  # 加收保證金指標
    security_collateral_amount: float  # 有價證券抵繳總額
    order_margin_premium: float  # 委託保證金及委託權利金
    collateral_amount: float  # 有價品額
