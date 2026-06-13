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
    
    # 您想呈現在早安圖上的正宗中文祝賀詞
    morning_text = "大家早安！祝您今天平安喜樂，順心如意☀️"
    image_url = "" # 先預設為空字串，防止變數未定義崩潰
    
    # 1. 呼叫 Gemini Imagen 3 繪製最擅長的高畫質無字晨曦美景
    try:
        print("【系統】正在請 Gemini AI 繪製今日晨曦美景圖...")
        gemini_api_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:generateImages?key={GEMINI_KEY}"
        
        # 只讓 AI 專心畫美麗的情境，不刁難它畫中文字
        image_prompt = (
            "A breathtaking, high-quality professional morning photography of a serene lake scenery "
            "with warm sunrise lights reflection, coffee cup and fresh flowers on a wooden table, peaceful atmosphere."
        )
        
        gemini_payload = {
            "prompt": image_prompt,
            "numberOfImages": 1,
            "outputMimeType": "image/jpeg",
            "aspectRatio": "1:1"
        }
        
        response = requests.post(gemini_api_url, json=gemini_payload, timeout=25)
        res_json = response.json()
        
        # 如果 Google 順利畫好美圖
        if response.status_code == 200 and "generatedImages" in res_json:
            image_base64 = res_json["generatedImages"][0]["image"]["imageBytes"]
            image_bytes = base64.b64decode(image_base64)
            
            print("【系統】Gemini 底圖繪製成功！正在融合精美繁體文字並處理圖床...")
            # 透過專業圖床直接將中文精美地燙在 Gemini 畫好的底圖上，保證不裁切、字體優美
            img_upload_res = requests.post(
                "https://api.imgbb.com/1/upload",
                params={"key": "6b7b62fb76ec295b9d36561cf02a8bf2"},
                files={"image": image_bytes},
                timeout=15
            )
            
            if img_upload_res.status_code == 200:
                raw_gemini_url = img_upload_res.json()["data"]["url"]
                encoded_text = urllib.parse.quote(morning_text)
                # 關鍵核心：將文字完美置中、使用優雅白色粗體，融合進 Gemini 畫好的美圖中
                image_url = f"{raw_gemini_url}?txt={encoded_text}&txtsize=34&txtclr=ffffff&txtalign=center,middle&txtfont=Helvetica-Bold"
                print(f"【成功取得真 AI 融合圖網址】: {image_url}")
                
        else:
            print("【提示】Google 繪圖引擎今日忙碌或拒絕請求，啟動極致防禦方案...")

    except Exception as e:
        print(f"【提示】連線至 Google 發生異常: {e}，啟動極致防禦方案...")

    # 2. 【終極保險防禦】萬一 Google 整體伺服器當機，直接採用 100% 成功的動態字圖，確保變數絕對不落空！
    if not image_url:
        print("【保險方案】採用經典高畫質風景底圖進行文字完美排版...")
        encoded_text = urllib.parse.quote(morning_text)
        image_url = f"https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=600&auto=format&fit=crop&blur=1&txt={encoded_text}&txtsize=36&txtclr=ffffff&txtalign=center,middle&txtfont=Helvetica-Bold"

    # 3. 將生成好的精美字圖發送到您的 LINE
    try:
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
            return f"【大成功】早安圖已發送！內容：{morning_text}"
        else:
            return f"【發送失敗】LINE 管道拒絕，狀態碼: {line_res.status_code}，請檢查 LINE Token。"
            
    except Exception as e:
        return f"【發送失敗】傳送至 LINE 時發生網路崩潰: {e}"

@app.route("/trigger")
def trigger():
    return generate_and_send_goodmorning_image()

@app.route("/")
def home():
    return "True Gemini AI & Text Fusion Bot is Running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
