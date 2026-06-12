import os
from flask import Flask
import requests
import google.generativeai as genai

app = Flask(__name__)

def send_morning_greeting():
    LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_USER_ID = os.environ.get("LINE_USER_ID")
    GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
    
    if not all([LINE_ACCESS_TOKEN, LINE_USER_ID, GEMINI_KEY]):
        return "【錯誤】環境變數設定不完整！"

    genai.configure(api_key=GEMINI_KEY)
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = "請寫一句溫馨、充滿正能量的早餐問候語（繁體中文），適合傳給群組的朋友。字數在30字以內，並適度加上 ☀️、☕、🌸 等貼圖表情。"
        response = model.generate_content(prompt)
        msg_text = response.text.strip()
    except Exception as e:
        msg_text = "大家早安！祝大家今天順心如意，活力滿滿！☀️"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": msg_text}]
    }
    
    url = "https://api.line.me/v2/bot/message/push"
    res = requests.post(url, headers=headers, json=payload)
    
    if res.status_code == 200:
        return "【大成功】早安訊息已發送！"
    else:
        return f"【發送失敗】錯誤碼: {res.status_code}"

# 建立一個網址網頁，只要有人造訪這個網址，就會觸發發送早安圖
@app.route("/trigger")
def trigger():
    result = send_morning_greeting()
    return result

# 首頁，用來給 Render 檢查主機有沒有活著
@app.route("/")
def home():
    return "Good Morning Bot is Running!"

if __name__ == "__main__":
    # 自動動態綁定 Render 的連接埠，解決 Port 報錯問題
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
