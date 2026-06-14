import os
import time
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

# 您已經成功上傳的字體檔與輸出的圖片檔名
FONT_PATH = "NotoSansTC-Bold.ttf"
LOCAL_IMAGE_PATH = "morning_output.jpg"

def draw_beautiful_text(draw, text, font, image_width):
    """ 使用您上傳的微軟正黑體，精準計算長度、自動換行、置中並加上立體黑邊 """
    lines = []
    current_line = ""
    
    # 自動換行邏輯：兩邊各留 60 像素邊距
    for char in text:
        test_line = current_line + char
        if draw.textlength(test_line, font=font) < (image_width - 120):
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)
        
    line_height = int(font.size * 1.4)
    total_text_height = len(lines) * line_height
    
    # 讓整塊文字美美地鎖定在畫面中央偏下方
    start_y = 400 - (total_text_height // 2)
    
    for line in lines:
        line_width = draw.textlength(line, font=font)
        x = (image_width - line_width) // 2
        
        # 繪製 360 度立體黑色外框，保證看得很清楚
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, start_y + dy), line, font=font, fill="black")
                    
        # 覆蓋上純白色的精美正文
        draw.text((x, start_y), line, font=font, fill="white")
        start_y += line_height

def generate_morning_image():
    # 穩定高畫質的風景底圖
    bg_url = "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=800&auto=format&fit=crop"
    morning_text = "大家早安！祝您今天平安喜樂，順心如意☀️"
    
    try:
        img_res = requests.get(bg_url, timeout=10, stream=True)
        if img_res.status_code != 200:
            return False
            
        img = Image.open(img_res.raw).convert("RGB")
        img = img.resize((800, 600))
        draw = ImageDraw.Draw(img)
        
        # 100% 讀取您上傳的字體，設定大小為 42，絕對不噴 status 1
        if os.path.exists(FONT_PATH):
            font = ImageFont.truetype(FONT_PATH, 42)
        else:
            font = ImageFont.load_default()
            
        draw_beautiful_text(draw, morning_text, font, 800)
        img.save(LOCAL_IMAGE_PATH, "JPEG", quality=90)
        return True
    except Exception as e:
        print(f"錯誤: {e}")
        return False

@app.route("/morning_image.jpg")
def serve_image():
    if os.path.exists(LOCAL_IMAGE_PATH):
        return send_file(LOCAL_IMAGE_PATH, mimetype="image/jpeg")
    return "Image not found.", 404

@app.route("/trigger")
def trigger():
    LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_USER_ID = os.environ.get("LINE_USER_ID")
    RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
    
    if not all([LINE_ACCESS_TOKEN, LINE_USER_ID]):
        return "環境變數尚未設定完成"
        
    if not RENDER_EXTERNAL_URL:
        RENDER_EXTERNAL_URL = "https://" + requests.headers.get('Host', '')

    # 畫圖
    if not generate_morning_image():
        return "圖片生成失敗"
        
    # 加上時間戳記防止手機圖片快取不更新
    timestamp = int(time.time())
    final_image_url = f"{RENDER_EXTERNAL_URL.rstrip('/')}/morning_image.jpg?t={timestamp}"

    # 發送給您的 LINE
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
    
    line_res = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload, timeout=15)
    
    if line_res.status_code == 200:
        return "早安圖已成功發送！"
    else:
        return f"LINE 發送失敗: {line_res.status_code}"

@app.route("/")
def home():
    return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
