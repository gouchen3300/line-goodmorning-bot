import os
import time
import random
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

FONT_PATH = "NotoSansTC-Bold.ttf"
LOCAL_IMAGE_PATH = "morning_output.jpg"

BACKUP_QUOTES = [
    "大家早安！新的一天，祝您心情愉快，萬事順心如意。",
    "早安！願您今天充滿活力，迎來滿滿的平安與喜樂。",
    "大家早安！把心靈迎向陽光，今天也是美好的一天。"
]

def get_gemini_morning_quote():
    """ 讓 Gemini AI 現場創作溫暖、純文字的早安金句 """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return random.choice(BACKUP_QUOTES)
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{
                "text": "你是一位充滿正能量的早安圖大師。請為我寫一句送給朋友的早安問候語。要求：必須包含「早安」或「大家早安」，語氣要溫暖、積極、充滿祝福。整句話請控制在 15 到 25 個字之間，絕對不要包含任何 Emoji 貼圖、不要引號、不要星號、不要任何特殊符號，只要純中文字。"
            }]
        }]
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            result = res.json()
            quote = result['candidates'][0]['content']['parts'][0]['text'].strip()
            quote = quote.replace('"', '').replace('「', '').replace('」', '').replace('\n', '')
            if quote:
                return quote
    except Exception as e:
        print(f"Gemini API 錯誤: {e}")
        
    return random.choice(BACKUP_QUOTES)

def draw_beautiful_text(draw, text, font_path, image_width):
    """ 動態排版：將「早安」獨立放大置頂，主文換行置中，並升級為鮮豔黃色字體 """
    # 1. 拆分「早安標題」與「正文祝福語」
    title_text = ""
    body_text = text
    
    for prefix in ["大家早安！", "大家早安", "早安！", "早安"]:
        if text.startswith(prefix):
            title_text = prefix
            body_text = text[len(prefix):].lstrip("，, ")
            break
            
    if not title_text:
        title_text = "早安！"

    # 2. 設定不同的字體大小
    title_font = ImageFont.truetype(font_path, 55)  # 早安二字加大凸顯！
    body_font = ImageFont.truetype(font_path, 38)   # 內文精緻適中

    lines = []
    current_line = ""
    
    # 內文自動換行邏輯
    for char in body_text:
        test_line = current_line + char
        if draw.textlength(test_line, font=body_font) < (image_width - 120):
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)

    # 計算總高度來做垂直置中（放在畫面中下方比較美）
    title_height = int(title_font.size * 1.5)
    body_line_height = int(body_font.size * 1.4)
    total_text_height = title_height + (len(lines) * body_line_height)
    
    start_y = 440 - (total_text_height // 2)

    # 3. 繪製特別凸顯的「早安標題」（使用亮眼純白 + 立體重黑邊）
    title_w = draw.textlength(title_text, font=title_font)
    title_x = (image_width - title_w) // 2
    for dx in [-3, -2, -1, 0, 1, 2, 3]:
        for dy in [-3, -2, -1, 0, 1, 2, 3]:
            if dx != 0 or dy != 0:
                draw.text((title_x + dx, start_y + dy), title_text, font=title_font, fill="black")
    draw.text((title_x, start_y), title_text, font=title_font, fill="#FFFFFF") # 純白
    
    start_y += title_height + 10 # 空一點間距

    # 4. 繪製「正文祝福語」（升級為鮮豔的黃金色 #FFD700）
    for line in lines:
        line_w = draw.textlength(line, font=body_font)
        x = (image_width - line_w) // 2
        
        # 黑色粗外框
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, start_y + dy), line, font=body_font, fill="black")
                    
        # 鮮豔字體顏色
        draw.text((x, start_y), line, font=body_font, fill="#FFD700") # 鮮豔金黃色
        start_y += body_line_height

def generate_morning_image(text_content):
    # 【升級：真正隨機風景圖】使用隨機關鍵字（如：日出、森林、晨光），每次下載的圖都完全不一樣！
    keywords = ["sunrise", "morning", "nature", "mountain", "forest", "sunlight"]
    selected_keyword = random.choice(keywords)
    bg_url = f"https://images.unsplash.com/featured/800x600/?{selected_keyword}"
    
    try:
        # 加上隨機數防止 API 快取舊圖
        img_res = requests.get(f"{bg_url}&sig={random.randint(1, 9999)}", timeout=15, stream=True)
        if img_res.status_code != 200:
            return False
            
        img = Image.open(img_res.raw).convert("RGB")
        img = img.resize((800, 600))
        draw = ImageDraw.Draw(img)
        
        # 呼叫精美文字排版
        if os.path.exists(FONT_PATH):
            draw_beautiful_text(draw, text_content, FONT_PATH, 800)
        else:
            font = ImageFont.load_default()
            draw.text((50, 250), text_content, font=font, fill="white")
            
        img.save(LOCAL_IMAGE_PATH, "JPEG", quality=92)
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

    ai_quote = get_gemini_morning_quote()

    if not generate_morning_image(ai_quote):
        return "圖片生成失敗"
        
    timestamp = int(time.time() * 1000) # 精細到毫秒，徹底解決手機快取不換圖的問題
    final_image_url = f"{RENDER_EXTERNAL_URL.rstrip('/')}/morning_image.jpg?t={timestamp}"

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
        return f"【成功】全新動態早安圖已發送！今日金句：{ai_quote}"
    else:
        return f"LINE 發送失敗: {line_res.status_code}"

@app.route("/")
def home():
    return "Gemini Dynamic Morning Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
