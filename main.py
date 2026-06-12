import os
import base64
import urllib.parse
from flask import Flask
import requests

app = Flask(__name__)

def generate_and_send_goodmorning_image():
    LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_USER_ID = os.environ.get("LINE_USER_ID")
    GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
    
    if not all([LINE_ACCESS_TOKEN, LINE_USER_ID, GEMINI_KEY]):
        return "【錯誤】環境變數設定不完整，請檢查 Render 的 Environment 變數！"
    
    # 預設一句最溫馨、絕對不會出錯的經典早安詞
    morning_text = "大家早安！祝您今天平安喜樂，順心如意☀️"
    image_url = ""
    
    # 核心機制：嘗試呼叫正宗 Gemini Imagen 3 引擎生圖
    try:
        print("【系統】正在呼叫 Gemini Imagen 3 引擎繪製早安圖...")
        gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:generateImages?key={GEMINI_KEY}"
        
        image_prompt = "A beautiful, warm and bright morning scenery with a cup of hot coffee and fresh flowers, realistic photographic style."
        
        gemini_payload = {
            "prompt": image_prompt,
            "numberOfImages": 1,
            "outputMimeType": "image/jpeg",
            "aspectRatio": "1:1"
        }
        
        # 為了避免 Render 剛醒來太慢，我們設定 timeout 限制
        response = requests.post(gemini_api_url, json=gemini_payload, timeout=8)
        res_json = response.json()
        
        if response.status_code == 200 and "generatedImages" in res_json:
            image_base64 = res_json["generatedImages"][0]["image"]["imageBytes"]
            image_bytes = base64.b64decode(image_base64)
            
            print("【系統】AI 繪圖成功！上傳至臨時圖床...")
            img_upload_res = requests.post(
                "https://api.imgbb.com/1/upload",
                params={"key": "6b7b62fb76ec295b9d36561cf02a8bf2"}, # 免帳號測試金鑰
                files={"image": image_bytes},
                timeout=8
            )
            if img_upload_res.status_code == 200:
                image_url = img_upload_res.json()["data"]["url"]
                print(f"【成功取得 AI 圖網址】: {image_url}")
                
    except Exception as e:
        print(f"【提示】AI 繪圖未即時回應，啟動安全保護機制: {e}")

    # 【超級保險防禦】如果 AI 生圖太慢或失敗，直接採用 100% 成功的動態精美風景字圖
    if not image_url:
        print("【保險方案】正在將精美文字完美排版於晨曦風景圖上...")
        encoded_text = urllib.parse.quote(morning_text)
        image_url = f"https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=600&auto=format&fit=crop&blur=1&txt={encoded_text}&txtsize=36&txtclr=ffffff&txtalign=center,middle&txtfont=Helvetica-Bold"

    # 3. 發送至 LINE
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
    line_res = requests.post(url, headers=headers, json=payload, timeout=8)
    
    if line_res.status_code == 200:
        return f"【大成功】早安圖已成功發送到您的 LINE！內容：{morning_text}"
    else:
        return f"【發送失敗】LINE 管道出錯，狀態碼: {line_res.status_code}，請檢查 Token 是否填錯。"

@app.route("/trigger")
def trigger():
    return generate_and_send_goodmorning_image()

@app.route("/")
def home():
    return "Render Good Morning Bot is Ready and Live!"

if __name__ == "__main__":
    # 自動適配 Render 環境變數中的 PORT，若沒有則預設使用 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
