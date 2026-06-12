import os
from flask import Flask
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
        print("【系統】正在呼叫 Gemini Imagen 3 直接繪製專屬早安圖...")
        
        # 這裡我們直接把早安詞的要求寫進生圖指令（Prompt）裡，讓它一體成型！
        image_prompt = (
            "A beautiful, warm and bright morning scenery with a cup of hot coffee and beautiful flowers, realistic photographic style. "
            "The image MUST clearly display the traditional Chinese text '祝你今天順心如意，活力滿滿！☀️' or '大家早安！☕' written elegantly on it."
        )
        
        # 直接使用最新的生圖模型
        imagen_model = genai.GenerativeModel('imagen-3.0-generate-002')
        result = imagen_model.generate_images(
            prompt=image_prompt,
            number_of_images=1,
            output_mime_type="image/jpeg",
            aspect_ratio="1:1"  # 正方形圖片，最適合 LINE 顯示
        )
        
        # 2. 將生成的圖片上傳到臨時圖床，轉換成 LINE 可以讀取的 URL
        image_bytes = result.generated_images[0].image.image_bytes
        
        print("【系統】正在將圖片上傳至臨時圖床...")
        img_upload_res = requests.post(
            "https://api.imgbb.com/1/upload",
            params={"key": "6b7b62fb76ec295b9d36561cf02a8bf2"}, # 免帳號測試金鑰
            files={"image": image_bytes}
        )
        
        if img_upload_res.status_code == 200:
            image_url = img_upload_res.json()["data"]["url"]
            print(f"【圖床網址取得】: {image_url}")
        else:
            return f"【錯誤】圖片上傳圖床失敗，錯誤碼: {img_upload_res.status_code}"

    except Exception as e:
        print(f"【生成失敗】原因: {e}")
        return f"【生成失敗】原因: {e}"

    # 3. 將「早安圖網址」透過 LINE 推播出去
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
    res = requests.post(url, headers=headers, json=payload)
    
    if res.status_code == 200:
        return "【大成功】Gemini 早安圖已成功發送至您的 LINE！"
    else:
        return f"【發送失敗】LINE 錯誤碼: {res.status_code}, 內容: {res.text}"

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
