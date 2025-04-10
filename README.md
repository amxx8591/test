# LINE BOT + InternLM3-8B (for Render)

## 使用說明
這是整合 LINE Messaging API 與 InternLM3-8B 模型的 Python 專案，可部署於 Render。

## 使用方式
1. 建立 LINE Channel 並設定 webhook 為 `/callback`
2. 設定下列環境變數：
   - LINE_CHANNEL_ACCESS_TOKEN
   - LINE_CHANNEL_SECRET
   - INTERNLM_API_TOKEN
3. 安裝套件並執行：
```bash
pip install -r requirements.txt
python app.py
