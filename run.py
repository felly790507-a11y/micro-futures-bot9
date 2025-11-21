# run.py
import asyncio, yaml, time, os
from loguru import logger
from src.data import replay_csv, Tick
from src.execu import ExecutorSim
from src.strategy import TwoTickStrategy

def load_cfg(path="configs/config.yml"):
    return yaml.safe_load(open(path, encoding="utf8"))

async def run_simulate(cfg):
    exe = ExecutorSim(cfg)
    strat = TwoTickStrategy(cfg, exe)
    csv_path = cfg.get("replay_csv", "data/sample_ticks.csv")
    for tick in replay_csv(csv_path):
        await strat.on_tick(tick)
        await asyncio.sleep(0.01)  # control replay speed

if __name__ == "__main__":
    cfg = load_cfg()
    logger.remove()
    logger.add(lambda msg: print(msg, end=""))
    if cfg["mode"] == "simulate":
        asyncio.run(run_simulate(cfg))
    else:
        print("Paper/live mode requires Shioaji executor. Implement ExecutorShioaji and subscription.")
