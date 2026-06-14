import os
import time
import random
import requests
import urllib.parse
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
    """ 讓 Gemini AI 現場創作富有畫面感的溫暖問候語 """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return random.choice(BACKUP_QUOTES)
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{
            "parts": [{
                "text": "你是一位充滿正能量的早安圖大師。請為我寫一句送給朋友的早安問候語。要求：必須包含「早安」或「大家早安」，語氣要溫暖、積極、富有詩意與畫面感。整句話請控制在 15 到 25 個字之間，絕對不要包含任何 Emoji 貼圖、不要引號、不要星號、不要任何特殊符號，只要純中文字。"
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
    """ 動態排版：早安放大置頂、主文換行置中、黃金字體 """
    title_text = ""
    body_text = text
    
    for prefix in ["大家早安！", "大家早安", "早安！", "早安"]:
        if text.startswith(prefix):
            title_text = prefix
            body_text = text[len(prefix):].lstrip("，, ")
            break
            
    if not title_text:
        title_text = "早安！"

    title_font = ImageFont.truetype(font_path, 55)
    body_font = ImageFont.truetype(font_path, 38)

    lines = []
    current_line = ""
    for char in body_text:
        test_line = current_line + char
        if draw.textlength(test_line, font=body_font) < (image_width - 120):
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)

    title_height = int(title_font.size * 1.5)
    body_line_height = int(body_font.size * 1.4)
    total_text_height = title_height + (len(lines) * body_line_height)
    
    start_y = 440 - (total_text_height // 2)

    # 繪製早安大字（白字加超粗黑邊，保證在任何 AI 圖片上都清晰可見）
    title_w = draw.textlength(title_text, font=title_font)
    title_x = (image_width - title_w) // 2
    for dx in [-3, -2, -1, 0, 1, 2, 3]:
        for dy in [-3, -2, -1, 0, 1, 2, 3]:
            draw.text((title_x + dx, start_y + dy), title_text, font=title_font, fill="black")
    draw.text((title_x, start_y), title_text, font=title_font, fill="#FFFFFF")
    
    start_y += title_height + 15

    # 繪製正文（鮮豔金黃色字體）
    for line in lines:
        line_w = draw.textlength(line, font=body_font)
        x = (image_width - line_w) // 2
        
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                draw.text((x + dx, start_y + dy), line, font=body_font, fill="black")
                    
        draw.text((x, start_y), line, font=body_font, fill="#FFD700")
        start_y += body_line_height

def generate_morning_image(text_content):
    """ 根據 Gemini 的文字，呼叫 AI 繪圖引擎現場『畫』出一張絕美、意境相符的全新底圖 """
    try:
        # 將中文字句加上「精美風景、唯美、高畫質」等繪圖關鍵字，並轉化為 AI 聽得懂的網址編碼
        prompt = f"beautiful serene landscape, masterpiece, high quality, matching the mood of: {text_content}"
        encoded_prompt = urllib.parse.quote(prompt)
        
        # 使用強大且免費的 Pollinations AI 繪圖接口（設定生成 800x600 的精美圖畫）
        ai_paint_url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=800&height=600&nologo=true&seed={random.randint(1, 99999)}"
        
        img_res = requests.get(ai_paint_url, timeout=25, stream=True)
        if img_res.status_code != 200:
            # 萬一 AI 繪圖伺服器塞車，使用大自然漸層綠當保底，絕對不報錯
            img = Image.new("RGB", (800, 600), color="#2E7D32")
        else:
            img = Image.open(img_res.raw).convert("RGB")
            img = img.resize((800, 600))
            
        draw = ImageDraw.Draw(img)
        
        if os.path.exists(FONT_PATH):
            draw_beautiful_text(draw, text_content, FONT_PATH, 800)
        else:
            font = ImageFont.load_default()
            draw.text((50, 250), text_content, font=font, fill="white")
            
        img.save(LOCAL_IMAGE_PATH, "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"AI 繪圖或圖片處理發生嚴重異常: {e}")
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

    # 1. 讓 Gemini 寫出當天獨一無二的金句
    ai_quote = get_gemini_morning_quote()

    # 2. 讓繪圖 AI 根據這句話現場「畫」出對應的精美背景
    if not generate_morning_image(ai_quote):
        return "圖片生成失敗"
        
    timestamp = int(time.time() * 1000)
    final_image_url = f"{RENDER_EXTERNAL_URL.rstrip('/')}/morning_image.jpg?t={timestamp}"

    # 3. 推送到您的 LINE
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
        return f"【成功】AI 現場繪製早安圖已發送！今日金句：{ai_quote}"
    else:
        return f"LINE 發送失敗: {line_res.status_code}"

@app.route("/")
def home():
    return "Gemini AI Painting Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
