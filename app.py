from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
import requests
import os
import base64

app = Flask(__name__)

# LINE credentials
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET')
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# InternVL API
INTERNVL_API_URL = 'https://chat.intern-ai.org.cn/api/v1/chat/completions'
INTERNVL_API_TOKEN = os.getenv('INTERNLM_API_TOKEN')

@app.route("/", methods=["GET"])
def home():
    return "LINE BOT with InternVL2.5 多模態模型 is running."

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
    reply_message = get_internvl_reply(user_message, None)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    image_content = line_bot_api.get_message_content(message_id)
    image_path = "temp.jpg"
    with open(image_path, "wb") as f:
        for chunk in image_content.iter_content():
            f.write(chunk)

    image_data_url = image_to_data_url(image_path)
    reply_message = get_internvl_reply("請描述這張圖片", image_data_url)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_message)
    )

def image_to_data_url(path):
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"

def get_internvl_reply(user_text, image_data_url=None):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {INTERNVL_API_TOKEN}'
    }

    content = [{"type": "text", "text": user_text}]
    if image_data_url:
        content.append({"type": "image_url", "image_url": {"url": image_data_url}})

    payload = {
        "model": "internvl2.5-chat",
        "messages": [{"role": "user", "content": content}],
        "temperature": 0.8,
        "top_p": 0.9
    }

    print("📸 payload:", payload)

    try:
        response = requests.post(INTERNVL_API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print("⚠️ InternVL 回傳錯誤：", response.status_code, response.text)
            return f"⚠️ 模型錯誤（{response.status_code}）：{response.text}"
    except Exception as e:
        return f"❌ 呼叫模型時發生錯誤：{str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
