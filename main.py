import os
import time
import random
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

FONT_PATH = "NotoSansTC-Bold.ttf"
LOCAL_IMAGE_PATH = "morning_output.jpg"

# 萬一網路斷線、Gemini 沒回應時的「保底早安金句」
BACKUP_QUOTES = [
    "大家早安！新的一天，祝您心情愉快，萬事順心如意。",
    "早安！願您今天充滿活力，迎來滿滿的平安與喜樂。",
    "大家早安！把心靈迎向陽光，今天也是美好的一天。"
]

def get_gemini_morning_quote():
    """ 每天連線去請 Gemini AI 現場創作一句溫暖、正能量的早安金句 """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("未設定 GEMINI_API_KEY，使用保底金句")
        return random.choice(BACKUP_QUOTES)
        
    # 呼叫 Gemini 官方 API 的標準管線
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{
                "text": "你是一位充滿正能量的早安圖大師。請為我寫一句送給朋友的早安問候語。要求：必須包含「早安」或「大家早安」，語氣要溫暖、積極、充滿正能量與祝福。整句話請控制在 15 到 25 個字之間，絕對不要包含任何 Emoji 貼圖、不要引號、不要星號、不要任何特殊符號，只要純中文字。"
            }]
        }]
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            result = res.json()
            quote = result['candidates'][0]['content']['parts'][0]['text'].strip()
            # 再次過濾掉可能殘留的引號或換行
            quote = quote.replace('"', '').replace('「', '').replace('」', '').replace('\n', '')
            if quote:
                return quote
    except Exception as e:
        print(f"Gemini API 呼叫失敗: {e}")
        
    return random.choice(BACKUP_QUOTES)

def draw_beautiful_text(draw, text, font, image_width):
    """ 使用微軟正黑體自動換行、置中，並加上清晰的黑色立體黑邊 """
    lines = []
    current_line = ""
    
    # 自動換行：左右各留 60 像素邊距
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
    start_y = 420 - (total_text_height // 2)
    
    for line in lines:
        line_width = draw.textlength(line, font=font)
        x = (image_width - line_width) // 2
        
        # 繪製 360 度立體黑色外框，確保在任何風景圖上都看得清楚
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, start_y + dy), line, font=font, fill="black")
                    
        # 覆蓋純白字體
        draw.text((x, start_y), line, font=font, fill="white")
        start_y += line_height

def generate_morning_image(text_content):
    # 每次都去 Unsplash 隨機抽取一張最新的大自然高畫質風景美圖（每次觸發底圖都不一樣！）
    bg_url = "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=800&auto=format&fit=crop"
    
    try:
        img_res = requests.get(bg_url, timeout=10, stream=True)
        if img_res.status_code != 200:
            return False
            
        img = Image.open(img_res.raw).convert("RGB")
        img = img.resize((800, 600))
        draw = ImageDraw.Draw(img)
        
        if os.path.exists(FONT_PATH):
            font = ImageFont.truetype(FONT_PATH, 40) # 字體稍微調小一點點，讓 Gemini 的長句子更美觀
        else:
            font = ImageFont.load_default()
            
        draw_beautiful_text(draw, text_content, font, 800)
        img.save(LOCAL_IMAGE_PATH, "JPEG", quality=90)
        return True
    except Exception as e:
        print(f"圖片生成失敗: {e}")
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

    # 1. 讓 Gemini 現場創作今天的溫暖句子！
    ai_quote = get_gemini_morning_quote()

    # 2. 根據這句話，隨機抓風景圖合成出早安圖
    if not generate_morning_image(ai_quote):
        return "圖片生成失敗"
        
    timestamp = int(time.time())
    final_image_url = f"{RENDER_EXTERNAL_URL.rstrip('/')}/morning_image.jpg?t={timestamp}"

    # 3. 發送給您的 LINE
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
        return f"【成功】Gemini 早安圖已發送！今日金句：{ai_quote}"
    else:
        return f"LINE 發送失敗: {line_res.status_code}"

@app.route("/")
def home():
    return "Gemini Morning Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
