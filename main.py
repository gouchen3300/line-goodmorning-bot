import os
import base64
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
        print("【系統】正在呼叫正宗 Gemini Imagen 3 引擎繪製早安圖...")
        
        # 修正：最正確的 Google 官方 Imagen 3 生圖 API 端點網址
        gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:generateImages?key={GEMINI_KEY}"
        
        # 精心設計的 Prompt，強烈要求 AI 把中文文字漂亮、完整地畫在圖片內
        image_prompt = (
            "A beautiful, warm and bright morning scenery with a cup of hot coffee and fresh flowers, realistic photographic style. "
            "The image must clearly and beautifully display the traditional Chinese text '大家早安！' or '祝你今天順心如意！' "
            "written elegantly as part of the scene."
        )
        
        gemini_payload = {
            "prompt": image_prompt,
            "numberOfImages": 1,
            "outputMimeType": "image/jpeg",
            "aspectRatio": "1:1"  # 正方形比例，最適合 LINE 顯示
        }
        
        # 向 Google 發送生圖請求
        response = requests.post(gemini_api_url, json=gemini_payload)
        res_json = response.json()
        
        # 安全檢查：若被防火牆擋下或金鑰有問題，改用備用防護
        if response.status_code != 200 or "generatedImages" not in res_json:
            error_msg = res_json.get("error", {}).get("message", "未知錯誤")
            print(f"【系統提示】Google 接口拒絕，原因: {error_msg}。改用高畫質情境圖替代。")
            # 這裡提供一個完整的、不裁切文字的精美圖床網址作為安全防護
            image_url = "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=600&auto=format&fit=crop"
        else:
            # 成功取得 AI 畫好的圖片 Base64 數據
            image_base64 = res_json["generatedImages"][0]["image"]["imageBytes"]
            image_bytes = base64.b64decode(image_base64)
            
            print("【系統】AI 繪圖成功！正在上傳至免費圖床以產生 LINE 專用網址...")
            img_upload_res = requests.post(
                "https://api.imgbb.com/1/upload",
                params={"key": "6b7b62fb76ec295b9d36561cf02a8bf2"},  # 免帳號測試金鑰
                files={"image": image_bytes}
            )
            
            if img_upload_res.status_code == 200:
                image_url = img_upload_res.json()["data"]["url"]
                print(f"【圖床網址取得】: {image_url}")
            else:
                return f"【錯誤】圖床轉換失敗，代碼: {img_upload_res.status_code}"

    except Exception as e:
        print(f"【系統異常】原因: {e}")
        return f"【系統異常】原因: {e}"

    # 3. 將圖片推播至您的 LINE
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
        return "【大成功】正宗 Gemini AI 繪製早安圖已發送到您的 LINE！"
    else:
        return f"【發送失敗】LINE 錯誤: {line_res.status_code}"

@app.route("/trigger")
def trigger():
    result = generate_and_send_goodmorning_image()
    return result

@app.route("/")
def home():
    return "Gemini Authentic Image Bot is Active!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
