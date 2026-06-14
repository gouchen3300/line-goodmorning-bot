import os
import time
import random
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io

app = Flask(__name__)

LOCAL_IMAGE_PATH = "morning_output.jpg"

# 保底罐頭文案（當 Gemini 偶爾出狀況時使用）
BACKUP_QUOTES = [
    "大家早安新的一天，祝您心情愉快萬事順心如意",
    "早安願您今天充滿活力，迎來滿滿的平安與喜樂",
    "大家早安把心靈迎向陽光，今天也是美好的一天"
]

# 鮮豔美觀的調色盤清單 (標題顏色, 內文顏色)
COLOR_PALETTES = [
    ("#FFFFFF", "#FFD700"),  # 經典款：純白標題 ＋ 亮眼金黃內文
    ("#FFFFFF", "#FF69B4"),  # 嬌豔款：純白標題 ＋ 鮮豔桃粉內文
    ("#FFFFFF", "#FF4500"),  # 活力款：純白標題 ＋ 太陽亮橘內文
    ("#FFFFFF", "#00FF7F"),  # 清爽款：純白標題 ＋ 螢光嫩綠內文
    ("#FFFFFF", "#00FFFF")   # 明亮款：純白標題 ＋ 璀璨明藍內文
]

# 台灣開源繁體中文字型雲端直連庫（包含黑體、明體、圓體、楷體）
FONT_URLS = [
    "https://raw.githubusercontent.com/ButTaiwan/genseki-font/master/font/Genseki-Bold.ttf",    # 源石黑體（穩重粗體）
    "https://raw.githubusercontent.com/ButTaiwan/genyo-font/master/font/GenYoMin-Bold.ttf",     # 源樣明體（優雅古典）
    "https://raw.githubusercontent.com/ButTaiwan/genwan-font/master/font/GenWanMin-Regular.ttf", # 源雲明體（文青詩意）
    "https://raw.githubusercontent.com/ButTaiwan/gensen-font/master/font/Gensen-Bold.ttf",     # 源泉圓體（圓潤可愛）
    "https://raw.githubusercontent.com/ButTaiwan/genseki-font/master/font/Genseki-Medium.ttf"  # 源石中黑（清晰好讀）
]

def get_gemini_morning_quote():
    """ 讓 Gemini 生成溫暖語句，並強制要求長度適中以便平均斷句 """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return random.choice(BACKUP_QUOTES)
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    random_topics = ["大自然晨光", "朝露與花朵", "心靈茶香", "微風與遠山", "希望與活力", "喜悅與相伴", "溫暖陽光"]
    selected_topic = random.choice(random_topics)
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"你是一位頂級的早安圖文學大師。請圍繞『{selected_topic}』這個意境，為我全新創作一句送給好友的早安問候語。要求：1. 必須包含「早安」或「大家早安」作為開頭。2. 總字數控制在 16 到 22 個字之間（字數越接近偶數越好）。3. 除去開頭的早安後，後面的文案中間必須包含一個全形逗號『，』，且逗號前後的字數要盡可能一樣多（做到左右對稱、字數平均）。4. 絕對不要有任何其他標點符號、不要 Emoji 貼圖。只要純中文字。"
            }]
        }]
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            result = res.json()
            quote = result['candidates'][0]['content']['parts'][0]['text'].strip()
            # 清除雜質符號
            for punc in ['。', '！', '、', '？', '；', '：', '.', '!', '?', '"', '「', '」', '*', '\n', ' ']:
                quote = quote.replace(punc, '')
            if quote:
                return quote
    except Exception as e:
        print(f"Gemini API 生成出錯: {e}")
        
    return random.choice(BACKUP_QUOTES)

def fetch_random_font(size):
    """ 從雲端字型庫中「隨機抽取」一款字型直接載入記憶體，實現每天自動變化字體 """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    # 隨機打亂字型順序，每次呼叫都可能抽到不同的字體
    chosen_url = random.choice(FONT_URLS)
    
    try:
        response = requests.get(chosen_url, headers=headers, timeout=15)
        if response.status_code == 200 and len(response.content) > 500000:
            font_bytes = io.BytesIO(response.content)
            return ImageFont.truetype(font_bytes, size)
    except Exception as e:
        print(f"雲端字型動態載入失敗，啟用保底機制: {e}")
        
    # 如果網路偶爾瞬斷，則使用 Pillow 預設（此時字體較一般，但確保不會壞掉）
    return ImageFont.load_default()

def draw_beautiful_text(draw, text, image_width):
    """ 完美的自動平均斷句排版 ＋ 隨機多變字體 """
    title_text = ""
    body_text = text
    
    for prefix in ["大家早安", "早安"]:
        if text.startswith(prefix):
            title_text = prefix
            body_text = text[len(prefix):]
            break
            
    if not title_text:
        title_text = "早安"

    # 動態取得隨機變化的中文字型
    title_font = fetch_random_font(58)
    body_font = fetch_random_font(36)

    # 隨機挑選一組鮮豔美觀的文字顏色組合
    title_color, body_color = random.choice(COLOR_PALETTES)

    # 【字數平均切半邏輯】
    # 如果有逗號，優先依據逗號拆分
    if "，" in body_text:
        lines = [line.strip() for line in body_text.split("，") if line.strip()]
    else:
        # 如果沒有逗號，則精準對半切，確保兩行字數一模一樣
        mid = len(body_text) // 2
        lines = [body_text[:mid], body_text[mid:]]

    # 計算黃金置中排版高度
    title_height = int(58 * 1.5)
    body_line_height = int(36 * 1.5)
    total_text_height = title_height + (len(lines) * body_line_height)
    start_y = 440 - (total_text_height // 2)

    # 繪製標題（立體超粗黑邊 ＋ 隨機鮮豔標題色）
    try:
        title_w = draw.textlength(title_text, font=title_font)
    except:
        title_w = len(title_text) * 58
    title_x = (image_width - title_w) // 2
    
    for dx in [-3, -2, -1, 0, 1, 2, 3]:
        for dy in [-3, -2, -1, 0, 1, 2, 3]:
            draw.text((title_x + dx, start_y + dy), title_text, font=title_font, fill="black")
    draw.text((title_x, start_y), title_text, font=title_font, fill=title_color)
    
    start_y += title_height + 25

    # 繪製平均分配的兩行內文（不帶標點符號）
    for line in lines:
        try:
            line_w = draw.textlength(line, font=body_font)
        except:
            line_w = len(line) * 36
        x = (image_width - line_w) // 2
        
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                draw.text((x + dx, start_y + dy), line, font=body_font, fill="black")
                    
        draw.text((x, start_y), line, font=body_font, fill=body_color)
        start_y += body_line_height

def generate_morning_image(text_content):
    """ 隨機匹配高畫質背景圖 """
    if any(k in text_content for k in ["陽光", "喜悅", "光芒", "微笑", "閃耀", "希望"]):
        url_pool = [
            f"https://picsum.photos/id/{random.choice([10, 28, 48, 54, 116])}/800/600",
            f"https://picsum.photos/id/{random.choice([192, 230, 235, 327, 404])}/800/600"
        ]
    else:
        url_pool = [
            f"https://picsum.photos/id/{random.choice([343, 364, 411, 444, 486])}/800/600",
            f"https://picsum.photos/id/{random.choice([522, 532, 593, 619, 650])}/800/600"
        ]
        
    bg_url = random.choice(url_pool)
    
    try:
        img_res = requests.get(bg_url, timeout=15, stream=True)
        if img_res.status_code != 200:
            fallback_url = "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?q=80&w=800"
            img_res = requests.get(fallback_url, timeout=10, stream=True)
            
        img = Image.open(img_res.raw).convert("RGB")
        img = img.resize((800, 600))
        img = img.filter(ImageFilter.GaussianBlur(radius=1.2)) # 柔焦
        
        draw = ImageDraw.Draw(img)
        draw_beautiful_text(draw, text_content, 800)
            
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
        return f"【成功】隨機多變字體早安圖已發送！今日金句：{ai_quote.replace('，', ' ')}"
    else:
        return f"LINE 發送失敗: {line_res.status_code}"

@app.route("/")
def home():
    return "Gemini Multi-Font Randomizer Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
