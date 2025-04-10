from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
import requests
import os
import easyocr

app = Flask(__name__)

# LINE credentials
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# InternLM API
INTERNLM_API_URL = 'https://chat.intern-ai.org.cn/api/v1/chat/completions'
INTERNLM_API_TOKEN = os.getenv('INTERNLM_API_TOKEN')

@app.route("/", methods=["GET"])
def home():
    return "LINE BOT with InternLM + OCR is running."

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

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    image_content = line_bot_api.get_message_content(message_id)
    image_path = f"temp.jpg"

    with open(image_path, "wb") as f:
        for chunk in image_content.iter_content():
            f.write(chunk)

    result = process_image(image_path)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result)
    )

def process_image(image_path):
    reader = easyocr.Reader(['ch_sim', 'en'])
    result = reader.readtext(image_path)
    if result:
        return "🔍 圖片中文字：\n" + "\n".join([r[1] for r in result])
    else:
        return "❌ 無法辨識圖片中的文字。"

def get_internlm_reply(user_message):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {INTERNLM_API_TOKEN}'
    }

    payload = {
        "model": "internvl2.5-latest",
        "messages": [{"role": "user", "content": user_message}],
        "temperature": 0.8,
        "top_p": 0.9
    }

    print("payload:", payload)

    try:
        response = requests.post(INTERNLM_API_URL, headers=headers, json=payload, timeout=20)

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print("⚠️ InternLM 回傳錯誤：", response.status_code, response.text)
            return f"⚠️ 模型錯誤（{response.status_code}）：{response.text}"
    except Exception as e:
        return f"❌ 呼叫模型時發生錯誤：{str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
