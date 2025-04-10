from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import requests
import os

app = Flask(__name__)

# LINE credentials (從環境變數讀取)
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# InternLM API 設定
INTERNLM_API_URL = 'https://chat.intern-ai.org.cn/api/v1/chat/completions'
INTERNLM_API_TOKEN = os.getenv('INTERNLM_API_TOKEN')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    reply_message = get_internlm_reply(user_message)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )

def get_internlm_reply(user_message):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {INTERNLM_API_TOKEN}'
    }
    payload = {
        "model": "internlm3-chat-8b",
        "messages": [{"role": "user", "content": user_message}],
        "temperature": 0.8,
        "top_p": 0.9
    }
    try:
        response = requests.post(INTERNLM_API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            return f"模型錯誤，代碼 {response.status_code}"
    except Exception as e:
        return f"模型回應異常：{e}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
