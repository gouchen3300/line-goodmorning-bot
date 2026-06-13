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
    
    try:
        print("【系統】第一步：呼叫 Gemini 文字大腦生成今天的溫馨祝詞...")
        
        # 1. 呼叫 Gemini 1.5 Flash 產生一句隨機的溫馨中文早安詞
        text_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
        text_payload = {
            "contents": [{
                "parts": [{
                    "text": "請生成一句適合放在長輩早安圖上的溫馨中文祝賀詞。字數控制在 10 到 15 個字以內，例如：『大家早安！祝您今天平安喜樂。』只要給我這句話本身，不要有任何引號、空格或解釋。"
                }]
            }]
        }
        
        # 允許等待 15 秒讓文字生成
        text_response = requests.post(text_api_url, json=text_payload, timeout=15)
        text_json = text_response.json()
        
        # 提取生成的中文祝福語
        try:
            morning_text = text_json['candidates'][0]['content']['parts'][0]['text'].strip()
        except:
            morning_text = "大家早安！祝您今天順心如意☀️" # 萬一文字失敗的極致備用
            
        print(f"【Gemini 文字生成成功】: {morning_text}")

        print("【系統】第二步：將文字與指令結合，呼叫 Gemini Imagen 3 引擎一體成型繪製...")
        
        # 2. 呼叫 Imagen 3 繪圖，強烈要求它把文字畫在圖裡面
        gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:generateImages?key={GEMINI_KEY}"
        
        # 完美的英文 Prompt 指令，指揮 AI 怎麼排版
        image_prompt = (
            "A breathtaking, high-quality professional morning photography of a serene lake scenery with sunrise lights reflection, peaceful atmosphere. "
            f"The image must clearly and beautifully display the traditional Chinese text '{morning_text}' "
            "written in an elegant, glowing font, masterfully blended into the sky or the center of the scene as a native part of the image, no typography errors."
        )
        
        gemini_payload = {
            "prompt": image_prompt,
            "numberOfImages": 1,
            "outputMimeType": "image/jpeg",
            "aspectRatio": "1:1" # 正方形最適合 LINE 閱讀
        }
        
        # 放寬等待時間到 30 秒，給 AI 充足的時間細心雕刻圖片
        response = requests.post(gemini_api_url, json=gemini_payload, timeout=30)
        res_json = response.json()
        
        if response.status_code == 200 and "generatedImages" in res_json:
            image_base64 = res_json["generatedImages"][0]["image"]["imageBytes"]
            image_bytes = base64.b64decode(image_base64)
            
            print("【系統】AI 繪圖大成功！正在上傳至臨時圖床...")
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
                return f"【錯誤】圖床轉換失敗，狀態碼: {img_upload_res.status_code}"
        else:
            error_info = res_json.get("error", {}).get("message", "未知原因")
            return f"【AI 生圖失敗】Google 拒絕請求，原因: {error_info}"

    except Exception as e:
        return f"【系統異常崩潰】請檢查網路或金鑰。錯誤原因: {e}"

    # 3. 發送至 LINE 管道
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
        return f"【真．AI 創作成功】早安圖已發送！文字為：{morning_text}"
    else:
        return f"【發送失敗】LINE 管道出錯，狀態碼: {line_res.status_code}"

@app.route("/trigger")
def trigger():
    return generate_and_send_goodmorning_image()

@app.route("/")
def home():
    return "True Gemini AI Good Morning Bot is Active!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
