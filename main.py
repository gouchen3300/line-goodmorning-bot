import os
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
        print("【系統】正在透過官方網頁接口呼叫 Imagen 3 繪製專屬早安圖...")
        
        # 這是發送給 Google 官方 Imagen 3 API 的網址
        gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:generateImages?key={GEMINI_KEY}"
        
        # 精心設計的早安圖指令
        image_prompt = (
            "A beautiful, warm and bright morning scenery with a cup of hot coffee and flowers, realistic photographic style. "
            "The image must clearly display the traditional Chinese text '大家早安！☀️' written elegantly on it."
        )
        
        # 依照官方標準規格準備資料
        gemini_payload = {
            "prompt": image_prompt,
            "numberOfImages": 1,
            "outputMimeType": "image/jpeg",
            "aspectRatio": "1:1"
        }
        
        # 直接向 Google 發送請求
        response = requests.post(gemini_api_url, json=gemini_payload)
        res_json = response.json()
        
        # 檢查 Google 是否有成功吐出圖片
        if response.status_code != 200 or "generatedImages" not in res_json:
            error_msg = res_json.get("error", {}).get("message", "未知原因")
            return f"【生成失敗】Google API 拒絕請求，原因: {error_msg}"
            
        # 提取圖片的 Base64 編碼，並轉換成二進位制檔案
        import base64
        image_base64 = res_json["generatedImages"][0]["image"]["imageBytes"]
        image_bytes = base64.b64decode(image_base64)
        
        # 2. 將生成的圖片上傳到臨時圖床，轉換成 LINE 可以讀取的 URL
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
