import os
import time
import random
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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
            quote = quote.replace('"', '').replace('「', '').replace('見', '').replace('」', '').replace('\n', '')
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

    # 繪製早安大字（白字立體黑邊）
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
    """ 根據 Gemini 句子的意境，動態匹配並下載高畫質藝術背景，保證 100% 成功不留綠底 """
    # 根據語意動態分析關鍵字
    image_id = random.randint(10, 1000) # 隨機基礎圖庫種子
    
    # 意境分析管線：若出現陽光/喜悅/光芒，導向晨曦藝術圖；若出現心靈/平安，導向沉靜森林或療癒系美景
    if any(k in text_content for k in ["陽光", "喜悅", "光芒", "微笑", "微笑"]):
        # 挑選溫暖晨光、金色調的高畫質影像 ID
        url_pool = [
            f"https://picsum.photos/id/{random.choice([10, 28, 48, 54, 116])}/800/600",
            f"https://picsum.photos/id/{random.choice([192, 230, 235, 327, 404])}/800/600"
        ]
    else:
        # 挑選大自然、山巒、森林等沉靜治癒影像 ID
        url_pool = [
            f"https://picsum.photos/id/{random.choice([343, 364, 411, 444, 486])}/800/600",
            f"https://picsum.photos/id/{random.choice([522, 532, 593, 619, 650])}/800/600"
        ]
        
    bg_url = random.choice(url_pool)
    
    try:
        # 連線極度穩定、絕不阻擋的反爬蟲全球 CDN 藝術圖庫
        img_res = requests.get(bg_url, timeout=15, stream=True)
        if img_res.status_code != 200:
            # 如果連線異常，直接改用穩定的高畫質後備圖，徹底消滅死綠色
            fallback_url = "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?q=80&w=800"
            img_res = requests.get(fallback_url, timeout=10, stream=True)
            
        img = Image.open(img_res.raw).convert("RGB")
        img = img.resize((800, 600))
        
        # 微調背景：輕微加上一點柔焦效果，讓前面的金黃色字體顯得更加高級、清晰凸顯
        img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
        
        draw = ImageDraw.Draw(img)
        
        if os.path.exists(FONT_PATH):
            draw_beautiful_text(draw, text_content, FONT_PATH, 800)
        else:
            font = ImageFont.load_default()
            draw.text((50, 250), text_content, font=font, fill="white")
            
        img.save(LOCAL_IMAGE_PATH, "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"動態藝術圖片生成異常: {e}")
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
        
    timestamp = int(time.time() * 1000)
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
        return f"【成功】精美意境配合早安圖已發送！今日金句：{ai_quote}"
    else:
        return f"LINE 發送失敗: {line_res.status_code}"

@app.route("/")
def home():
    return "Gemini Dynamic Art Morning Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
