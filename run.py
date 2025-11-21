import json
import os

# load config.json
cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
with open(cfg_path, "r", encoding="utf8") as f:
    cfg = json.load(f)

mode = cfg.get("mode", "simulate")

# 如果不是模擬模式才嘗試登入 shioaji
api = None
if mode != "simulate":
    import shioaji as sj
    try:
        # simulation=True 表示 paper 模擬環境；實盤請設定 simulation=False 並確認帳戶權限
        api = sj.Shioaji(simulation=True)
        api.login(api_key=cfg["api_key"], secret_key=cfg["secret_key"])
        print("✅ Shioaji 登入成功（simulation=True）")
    except Exception as e:
        print("❌ Shioaji 登入失敗:", e)
        api = None
else:
    print("模擬模式啟動（simulate），未嘗試登入 Shioaji")
