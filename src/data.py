# src/data.py
import csv
import time
from dataclasses import dataclass

@dataclass
class Tick:
    ts: float
    price: float
    qty: int
    side: str

def replay_csv(path):
    """蝪∪??? generator嚗SV 甈?: ts,price,qty,side"""
    with open(path, newline="", encoding="utf8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            yield Tick(ts=float(r["ts"]), price=float(r["price"]), qty=int(r["qty"]), side=r["side"])
