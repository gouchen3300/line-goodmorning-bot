import os
import requests
from flask import Flask

app = Flask(__name__)

def generate_ai_morning_image():
    LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_USER_ID = os.environ.get("LINE_USER_ID")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") # 請確保 Render 節點有設定您的 Gemini Key
    
    if not all([LINE_ACCESS_TOKEN, LINE_USER_ID, GEMINI_API_KEY]):
        return "【錯誤】環境變數（LINE 或 Gemini API Key）設定不完整！"
    
    # 告訴 Google Imagen 3 繪圖模型的指令 (中英文並用效果最好)
    # 這裡直接讓 AI 把中文美美地融入圖片裡！
    prompt = (
        "A beautiful, high-quality morning sunrise landscape with text written on it. "
        "The image should be warm, peaceful, and inspiring. "
        "In the center of the image, the following Chinese text must be beautifully and clearly displayed in a clean white font: "
        "'大家早安！祝您今天平安喜樂，順心如意☀️'"
    )
    
    try:
        print("【系統】正在呼叫 Google Imagen 3 繪圖模型生成藝術早安圖...")
        
        # 呼叫 Google 官方的 Image Generation API 節點
        imagen_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:generateImages?key={GEMINI_API_KEY}"
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "prompt": prompt,
            "numberOfImages": 1,
            "outputMimeType": "image/jpeg",
            "aspectRatio": "4:3"
        }
        
        response = requests.post(imagen_url, headers=headers, json=payload, timeout=30)
        res_json = response.json()
        
        # 解析 AI 生成的圖片 Base64 數據
        if response.status_code == 200 and "generatedImages" in res_json:
            img_base64 = res_json["generatedImages"][0]["image"]["imageBytes"]
            print("【系統】AI 藝術圖生成成功！正在上傳至 ImgBB 圖床...")
            
            # 將圖片轉傳至 ImgBB 換取 LINE 需要的網址
            img_upload_res = requests.post(
                "https://api.imgbb.com/1/upload",
                params={"key": "6b7b62fb76ec295b9d36561cf02a8bf2"},
                data={"image": img_base64},
                timeout=20
            )
            
            if img_upload_res.status_code == 200:
                final_image_url = img_upload_res.json()["data"]["url"]
                print(f"【AI 早安圖網址】: {final_image_url}")
            else:
                return "【圖床錯誤】上傳失敗。"
        else:
            error_msg = res_json.get("error", {}).get("message", "未知原因")
            return f"【AI 生圖失敗】原因: {error_msg}。請確認您的 API Key 是否支援 Imagen 3 模型。"
            
    except Exception as e:
        return f"【系統異常】{e}"

    # 发送至 LINE
    line_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    line_payload = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "image",
                "originalContentUrl": final_image_url,
                "previewImageUrl": final_image_url
            }
        ]
    }
    
    line_res = requests.post("https://api.line.me/v2/bot/message/push", headers=line_headers, json=line_payload, timeout=15)
    
    if line_res.status_code == 200:
        return "【大成功】AI 級藝術早安圖已發送到您的 LINE！"
    else:
        return f"【發送失敗】LINE 管道拒絕，狀態碼: {line_res.status_code}"

@app.route("/trigger")
def trigger():
    return generate_ai_morning_image()

@app.route("/")
def home():
    return "Imagen 3 AI Morning Bot is Running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
