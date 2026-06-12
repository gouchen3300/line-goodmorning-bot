import os
import urllib.parse
from flask import Flask
import requests

app = Flask(__name__)

def generate_and_send_goodmorning_image():
    LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_USER_ID = os.environ.get("LINE_USER_ID")
    GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
    
    if not all([LINE_ACCESS_TOKEN, LINE_USER_ID, GEMINI_KEY]):
        return "【錯誤】環境變數設定不完整！"
    
    try:
        print("【系統】正在請 Gemini 想一句最暖心的早安問候語...")
        
        # 1. 呼叫最穩定的 Gemini 文字接口想台詞
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        gemini_payload = {
            "contents": [{
                "parts": [{"text": "請寫一句溫馨、充滿正能量、適合長輩群組的早餐問候語（繁體中文）。字數在15字以內，結尾要加上1個貼圖如☀️或☕，不要任何說明。"}]
            }]
        }
        
        res = requests.post(gemini_url, json=gemini_payload)
        res_json = res.json()
        
        # 取出台詞
        morning_text = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"【Gemini 今日台詞】: {morning_text}")
        
        # 2. 呼叫全自動圖床：把「台詞」直接跟美麗的「日出風景圖」融合成早安圖
        # 我們使用優質的 Unsplash 晨曦高畫質圖，加上文字遮罩
        encoded_text = urllib.parse.quote(morning_text)
        
        # 這是一個極速高畫質圖片產生接口，會把文字優美地排版在精美的晨曦咖啡圖片上
        image_url = f"https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=600&auto=format&fit=crop&blur=2&txt={encoded_text}&txtsize=42&txtclr=ffffff&txtalign=center,middle&txtfont=Helvetica-Bold"
        print(f"【自動早安圖網址】: {image_url}")

    except Exception as e:
        print(f"【生成失敗】原因: {e}")
        return f"【生成失敗】原因: {e}"

    # 3. 將這張完美的早安圖透過 LINE 推播出去
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
        return f"【大成功】Gemini 專屬早安圖已發送！今日主題：{morning_text}"
    else:
        return f"【發送失敗】LINE 錯誤碼: {line_res.status_code}, 內容: {line_res.text}"

@app.route("/trigger")
def trigger():
    result = generate_and_send_goodmorning_image()
    return result

@app.route("/")
def home():
    return "Gemini Dynamic Image Bot is Active!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
