import os
import random
import urllib.parse
from flask import Flask
import requests

app = Flask(__name__)

# 準備一套精選的經典早安詞庫，當 Google API 鬧脾氣時自動拿來當後備保險！
BACKUP_GREETINGS = [
    "大家早安！祝你今天順心如意，活力滿滿☀️",
    "新的一天，從微笑開始！祝您平安喜樂☕",
    "美好的一天，送上最溫馨的問候，早安吉祥🌸",
    "幸福就是每天醒來都有好心情，祝您天天開心晨安✨",
    "願你帶著滿滿的正能量，迎接美好的一天！早安🌻"
]

def generate_and_send_goodmorning_image():
    LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_USER_ID = os.environ.get("LINE_USER_ID")
    GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
    
    if not all([LINE_ACCESS_TOKEN, LINE_USER_ID, GEMINI_KEY]):
        return "【錯誤】環境變數設定不完整！"
    
    morning_text = ""
    
    # 1. 嘗試呼叫 Gemini 想台詞
    try:
        print("【系統】正在嘗試向 Gemini 請教今日早安問候語...")
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        gemini_payload = {
            "contents": [{
                "parts": [{"text": "請寫一句給長輩群組的早餐問候語（繁體中文），字數在15字以內，結尾加上1個顏文字貼圖。只要回覆這句話，不要任何說明或符號。"}]
            }]
        }
        
        res = requests.post(gemini_url, json=gemini_payload, timeout=5)
        res_json = res.json()
        
        # 檢查 Google 回傳是否正常
        if "candidates" in res_json and len(res_json["candidates"]) > 0:
            morning_text = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
            print(f"【成功】Gemini 生成台詞: {morning_text}")
        else:
            print("【提示】Google 接口回傳異常，啟動安全防禦機制...")
    
    except Exception as e:
        print(f"【提示】Gemini 連線異常 ({e})，啟動安全防禦機制...")
    
    # 保險機制：如果 Gemini 失敗了，自動從台詞庫隨機抓一句，確保 100% 成功！
    if not morning_text:
        morning_text = random.choice(BACKUP_GREETINGS)
        print(f"【安全機制啟動】使用經典庫台詞: {morning_text}")

    # 2. 將台詞和 Unsplash 風景結合（使用安全的排版轉碼）
    try:
        encoded_text = urllib.parse.quote(morning_text)
        # 精美晨曦咖啡背景，並將文字置中
        image_url = f"https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=600&auto=format&fit=crop&blur=2&txt={encoded_text}&txtsize=38&txtclr=ffffff&txtalign=center,middle&txtfont=Helvetica-Bold"
        print(f"【早安圖生成網址】: {image_url}")
        
    except Exception as e:
        return f"【製圖失敗】原因: {e}"

    # 3. 將圖片推播至 LINE
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    
    payload = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "image",
                "originalContentUrl": image_url,
                "previewImageUrl": image_url
            }
        ]
    }
    
    url = "https://api.line.me/v2/bot/message/push"
    line_res = requests.post(url, headers=headers, json=payload)
    
    if line_res.status_code == 200:
        return f"【大成功】早安圖已發送！今日主題：{morning_text}"
    else:
        return f"【發送失敗】LINE 管道出錯，錯誤碼: {line_res.status_code}, 內容: {line_res.text}"

@app.route("/trigger")
def trigger():
    result = generate_and_send_goodmorning_image()
    return result

@app.route("/")
def home():
    return "Gemini Anti-Error Bot is Active!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
