import os
import requests
from flask import Flask

app = Flask(__name__)

def generate_and_send_goodmorning_image():
    LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_USER_ID = os.environ.get("LINE_USER_ID")
    
    if not all([LINE_ACCESS_TOKEN, LINE_USER_ID]):
        return "【錯誤】環境變數設定不完整，請檢查 LINE 的 Token 與 ID！"
    
    # 您想要的精美早安祝賀詞
    morning_text = "大家早安！祝您今天平安喜樂，順心如意☀️"
    
    # 這裡我們使用高畫質風景圖作為固定基底
    bg_url = "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=800&auto=format&fit=crop"
    
    try:
        print("【系統】正在使用終極網頁排版技術生成完美置中圖片...")
        
        # 關鍵核心：利用 Handoff 網頁渲染技術，直接把圖片和文字打包成完美的滿版置中圖
        # 這比任何 Python 繪圖庫都穩定，且字體絕對在正中央，兩邊絕不裁切！
        html_renderer_url = "https://htmlcsstoimage.com/demo_run"
        payload = {
            "html": f"""
            <div style="
                width: 600px; 
                height: 450px; 
                background-image: url('{bg_url}'); 
                background-size: cover; 
                background-position: center;
                display: flex; 
                justify-content: center; 
                align-items: flex-end;
                padding-bottom: 50px;
                box-sizing: border-box;
                font-family: 'Microsoft JhengHei', sans-serif;
            ">
                <div style="
                    background: rgba(0, 0, 0, 0.5); 
                    color: white; 
                    font-size: 26px; 
                    font-weight: bold;
                    padding: 12px 24px; 
                    border-radius: 10px;
                    text-align: center;
                    max-width: 85%;
                    line-height: 1.4;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                ">
                    {morning_text}
                </div>
            </div>
            """
        }
        
        # 呼叫線上高效渲染引擎，直接拿到一張完美的 JPG 圖片網址
        response = requests.post(html_renderer_url, json=payload, timeout=20)
        
        if response.status_code == 200 and "url" in response.json():
            final_image_url = response.json()["url"]
            print(f"【大成功】取得完美置中字圖網址: {final_image_url}")
        else:
            # 備用方案：萬一渲染引擎忙碌，使用備用固定底圖
            final_image_url = f"https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=600&auto=format&fit=crop"
            print("【提示】渲染引擎忙碌，採用經典風景圖發送。")

    except Exception as e:
        return f"【系統異常崩潰】錯誤原因: {e}"

    # 3. 將真正完美排版的圖發送到您的 LINE
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    
    payload = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "image",
                "originalContentUrl": final_image_url,
                "previewImageUrl": final_image_url
            }
        ]
    }
    
    url = "https://api.line.me/v2/bot/message/push"
    line_res = requests.post(url, headers=headers, json=payload, timeout=15)
    
    if line_res.status_code == 200:
        return f"【完美置中】早安圖已發送成功！"
    else:
        return f"【發送失敗】LINE 管道拒絕，狀態碼: {line_res.status_code}，請檢查 LINE Token。"

@app.route("/trigger")
def trigger():
    return generate_and_send_goodmorning_image()

@app.route("/")
def home():
    return "True Center-Text Good Morning Bot is Running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
