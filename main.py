import os
import time
from flask import Flask, request
import requests
import google.generativeai as genai

app = Flask(__name__)

def generate_and_send_goodmorning_image():
    LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_USER_ID = os.environ.get("LINE_USER_ID")
    GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
    
    if not all([LINE_ACCESS_TOKEN, LINE_USER_ID, GEMINI_KEY]):
        return "【錯誤】環境變數設定不完整！"

    # 1. 初始化 Gemini API
    genai.configure(api_key=GEMINI_KEY)
    
    try:
        # 2. 先請 Gemini 1.5 想一句溫馨的文字台詞
        text_model = genai.GenerativeModel('gemini-1.5-flash')
        text_prompt = "請寫一句溫馨、充滿正能量的早餐問候語（繁體中文），適合傳給群組的朋友。字數在20字以內。"
        text_response = text_model.generate_content(text_prompt)
        morning_text = text_response.text.strip()
        print(f"【台詞生成成功】: {morning_text}")
        
        # 3. 呼叫 Gemini 的生圖大腦 (Imagen 3) 繪製早安圖
        # 這裡會請 AI 把剛才想出來的文字畫在圖片上
        print("【系統】正在呼叫 Gemini Imagen 3 繪製專屬早安圖...")
        image_prompt = f"A beautiful, warm and bright morning scenerary, a cup of coffee and fresh flowers, realistic photographic style. The image must contain the traditional Chinese text: '{morning_text}' written elegantly."
        
        # 使用最新的 imagen-3.0-generate-002 模型
        imagen_model = genai.GenerativeModel('imagen-3.0-generate-002')
        result = imagen_model.generate_images(
            prompt=image_prompt,
            number_of_images=1,
            output_mime_type="image/jpeg",
            aspect_ratio="1:1" # 正方形圖片，最適合 LINE 顯示
        )
        
        # 4. 將生成的圖片轉換成 LINE 可以讀取的網路圖片網址
        # 因為 LINE 官方規範：推播圖片必須是一個公開的網址(URL)。
        # 這裡我們先借用免費的圖床 API (例如 Imgur 或其他免帳號圖床) 把圖片傳上去，拿到網址。
        image_bytes = result.generated_images[0].image.image_bytes
        
        print("【系統】正在將圖片上傳至臨時圖床...")
        img_upload_res = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": "6b7b62fb76ec295b9d36561cf02a8bf2"}, # 這是一把公開的免帳號測試鑰匙
            files={"image": image_bytes}
        )
        
        if img_upload_res.status_code == 200:
            image_url = img_upload_res.json()["data"]["url"]
            print(f"【圖床網址取得】: {image_url}")
        else:
            return "【錯誤】圖片上傳圖床失敗"

    except Exception as e:
        print(f"【生成失敗】原因: {e}")
        return f"【生成失敗】原因: {e}"

    # 5. 將「早安圖網址」透過 LINE 推播出去
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    
    # 這裡的格式從原本的 text 改成了 image！
    payload = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "image",
                "originalContentUrl": image_url, # 點開看的大圖
                "previewImageUrl": image_url      # 聊天室預覽的小圖
            }
        ]
    }
    
    url = "https://api.line.me/v2/bot/message/push"
    res = requests.post(url, headers=headers, json=payload)
    
    if res.status_code == 200:
        return "【大成功】Gemini 早安圖已成功發送至您的 LINE！"
    else:
        return f"【發送失敗】LINE 錯誤碼: {res.status_code}"

@app.route("/trigger")
def trigger():
    result = generate_and_send_goodmorning_image()
    return result

@app.route("/")
def home():
    return "Gemini Image Bot is Active!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
