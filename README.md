# micro-futures-bot

最小可運作的秒級 tick 自動交易骨架（3-tick -> kBAR，two-tick 偵測，IOC probe）。

快速開始:
1. 把專案放在 F:\期貨\micro-futures-bot
2. 建 virtualenv，安裝 requirements: pip install -r requirements.txt
3. 編輯 configs/config.yml（先用 mode: simulate）
4. run: python run.py

目錄說明:
- configs/: 環境設定
- src/: 程式模組（data, signal, state, execu, strategy）
- data/: 測試/回放用 tick CSV 檔
- logs/: 事件、下單記錄
- tests/: 單元測試

注意:
- 在切 paper/live 前，務必於 simulate 模式完成回放與小倉位測試
- 若要接 shioaji，請確認本地 shioaji 版本與權限（paper/live）
