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
        return "【錯誤】環境變數設定不完整，請檢查 Render 的 Environment 變數！"
    
    # 事先設定好您最想要的溫馨正宗中文祝賀詞
    morning_text = "大家早安！祝您今天平安喜樂，順心如意☀️"
    
    try:
        print("【系統】正在呼叫 Gemini Imagen 3 繪圖與文字排版大腦...")
        gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:generateImages?key={GEMINI_KEY}"
        
        # 終極 Prompt 指令：強烈命令 AI 將這句中文完美融合進畫面中，文字絕不裁切、字體要精美
        image_prompt = (
            "A breathtaking, high-quality professional morning photography of a serene lake scenery with warm sunrise lights reflection, peaceful and elegant atmosphere. "
            f"The image must clearly and beautifully display the traditional Chinese characters: '{morning_text}'. "
            "The text should be written in a sophisticated, glowing white, elegant font, masterfully blended into the sky or the center of the scene as a native part of the artwork. "
            "Ensure no text is cut off at the edges and no typography errors."
        )
        
        gemini_payload = {
            "prompt": image_prompt,
            "numberOfImages": 1,
            "outputMimeType": "image/jpeg",
            "aspectRatio": "1:1" # 正方形最適合 LINE 滿版呈現
        }
        
        # 給予充足的 45 秒讓 Render 等待 Google AI 刻畫精美圖片
        response = requests.post(gemini_api_url, json=gemini_payload, timeout=45)
        res_json = response.json()
        
        if response.status_code == 200 and "generatedImages" in res_json:
            image_base64 = res_json["generatedImages"][0]["image"]["imageBytes"]
            image_bytes = base64.b64decode(image_base64)
            
            print("【系統】Gemini AI 繪圖大成功！正在處理臨時圖床...")
            img_upload_res = requests.post(
                "https://api.imgbb.com/1/upload",
                params={"key": "6b7b62fb76ec295b9d36561cf02a8bf2"},
                files={"image": image_bytes},
                timeout=15
            )
            
            if img_upload_res.status_code == 200:
                image_url = img_upload_res.json()["data"]["url"]
                print(f"【成功取得 AI 融合圖網址】: {image_url}")
            else:
                return f"【圖床錯誤】上傳失敗，狀態碼: {img_upload_res.status_code}"
        else:
            error_info = res_json.get("error", {}).get("message", "未知原因，可能 API Key 需重新驗證")
            return f"【AI 生圖失敗】Google 拒絕請求，原因: {error_info}"

    except Exception as e:
        return f"【系統異常崩潰】錯誤原因: {e}"

    # 3. 將生成好的真正 AI 藝術字圖發送到您的 LINE
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
    line_res = requests.post(url, headers=headers, json=payload, timeout=15)
    
    if line_res.status_code == 200:
        return f"【真．Gemini AI 創作成功】正宗 AI 早安圖已發送！祝賀詞：{morning_text}"
    else:
        return f"【發送失敗】LINE 管道出錯，狀態碼: {line_res.status_code}"

@app.route("/trigger")
def trigger():
    return generate_and_send_goodmorning_image()

@app.route("/")
def home():
    return "True Gemini AI Graphic Bot is Running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
