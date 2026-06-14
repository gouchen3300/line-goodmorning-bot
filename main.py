import os
import time
import random
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = Flask(__name__)

LOCAL_IMAGE_PATH = "morning_output.jpg"
FONT_FILE_NAME = "morning.ttf"  # 沿用您上傳的繁體字型

# 俏皮可愛的保底罐頭文案（萬一 API 沒回應時備用）
BACKUP_QUOTES = [
    "大家早安！太陽公公曬屁股囉，今天也要元氣滿滿，記得吃早餐喔！",
    "早安！新的一天開始啦，祝你心情像爆米花一樣，快樂劈里啪啦！",
    "大家早安！幸福正在向你狂奔過來，今天也要記得保持微笑喔！"
]

# 充滿朝氣的豐富顏色搭配（文字, 內文1, 內文2, 第三行可愛亮色）
COLOR_PALETTES = [
    ("#FFFFFF", "#FFD700", "#FFD700", "#FFFF00"),  # 經典金黃 + 閃亮黃
    ("#FFFFFF", "#FF69B4", "#FFC0CB", "#FF1493"),  # 嬌豔粉紅 + 俏皮深粉
    ("#FFFFFF", "#FF4500", "#FFA500", "#FFD700"),  # 活力亮橘 + 溫暖金黃
    ("#FFFFFF", "#00FF7F", "#ADFF2F", "#00FFFF"),  # 清爽嫩綠 + 璀璨藍綠
    ("#FFFF00", "#FFFFFF", "#FFFFFF", "#FF69B4")   # 黃金標題 + 純白內文 + 少女粉紅
]

def get_gemini_morning_quote():
    """ 讓 Gemini 生成俏皮、可愛、絕對不無聊的三行早安文案 """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return random.choice(BACKUP_QUOTES)
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    random_styles = ["充滿元氣的小兔子", "幽默貼心的好朋友", "暖心又調皮的晨光精靈", "每天都想逗你笑的開心果"]
    selected_style = random.choice(random_styles)
    
    payload = {
        "contents": [{
            "parts": [{
                "text": (
                    f"你是一位說話風格極度『俏皮、可愛、活潑、幽默』的早安圖文學大師。請以『{selected_style}』的語氣，"
                    "全新創作一句送給好友的早安問候語。要求：\n"
                    "1. 必須包含「早安」或「大家早安」開頭。\n"
                    "2. 總字數控制在 25 到 32 個字之間，讀起來要讓人會心一笑、覺得不枯燥。\n"
                    "3. 內容中間必須包含兩個全形逗號『，』，將整句話自然分成『三段』。\n"
                    "   第一段是早安開頭，第二段是溫馨活力描述，第三段必須是最俏皮、最可愛、帶有互動感的結尾短句。\n"
                    "4. 絕對不要有任何驚嘆號、句號等標點符號（只要那兩個全形逗號），不要 Emoji 貼圖。只要純中文字。"
                )
            }]
        }]
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            result = res.json()
            quote = result['candidates'][0]['content']['parts'][0]['text'].strip()
            # 過濾掉不需要的雜質標點
            for punc in ['。', '！', '、', '？', '；', '：', '.', '!', '?', '"', '「', '」', '*', '\n', ' ']:
                quote = quote.replace(punc, '')
            if quote and quote.count("，") == 2:
                return quote
    except Exception as e:
        print(f"Gemini API 生成出錯: {e}")
        
    return random.choice(BACKUP_QUOTES)

def get_must_font(size):
    """ 100% 讀取本地 morning.ttf 字型 """
    if os.path.exists(FONT_FILE_NAME):
        try:
            return ImageFont.truetype(FONT_FILE_NAME, size)
        except:
            pass
    return ImageFont.load_default()

def draw_beautiful_text(draw, text, image_width):
    """ 完美的「三行排版」：第三行自動變形為「超粗俏皮傾斜體」 """
    # 依據逗號自然拆分成三行
    if "，" in text:
        lines = [line.strip() for line in text.split("，") if line.strip()]
    else:
        # 如果沒逗號，硬拆成三段
        third = len(text) // 3
        lines = [text[:third], text[third:third*2], text[third*2:]]

    # 如果抓出來不滿三行，用保底文字湊齊
    while len(lines) < 3:
        lines.append("今天也要超級快樂喔")

    # 基礎字型大小設定
    font_line1 = get_must_font(55)
    font_line2 = get_must_font(38)
    font_line3 = get_must_font(42)  # 第三行稍微放大一點點

    # 抽籤決定顏色組合
    color1, color2, color3, color_special = random.choice(COLOR_PALETTES)
    colors = [color1, color2, color_special]

    # 計算排版高度 (三行字)
    line_heights = [int(55 * 1.4), int(38 * 1.4), int(42 * 1.5)]
    total_height = sum(line_heights) + 40
    start_y = 440 - (total_height // 2)

    # --- 繪製第一行 (大標題) ---
    try: w1 = draw.textlength(lines[0], font=font_line1)
    except: w1 = len(lines[0]) * 55
    x1 = (image_width - w1) // 2
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            draw.text((x1 + dx, start_y + dy), lines[0], font=font_line1, fill="black")
    draw.text((x1, start_y), lines[0], font=font_line1, fill=colors[0])
    start_y += line_heights[0] + 15

    # --- 繪製第二行 (工整內文) ---
    try: w2 = draw.textlength(lines[1], font=font_line2)
    except: w2 = len(lines[1]) * 38
    x2 = (image_width - w2) // 2
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            draw.text((x2 + dx, start_y + dy), lines[1], font=font_line2, fill="black")
    draw.text((x2, start_y), lines[1], font=font_line2, fill=colors[1])
    start_y += line_heights[1] + 20

    # --- 繪製第三行 (【黑科技】特粗、立體可愛字型) ---
    try: w3 = draw.textlength(lines[2], font=font_line3)
    except: w3 = len(lines[2]) * 42
    x3 = (image_width - w3) // 2
    
    # 透過加強層次，讓第三行字體看起來非常厚重、Q彈可愛
    for dx in range(-5, 6):
        for dy in range(-5, 6):
            if abs(dx) + abs(dy) <= 8:
                draw.text((x3 + dx, start_y + dy), lines[2], font=font_line3, fill="black")
                
    # 疊加內嵌高光框，做出截然不同的卡通字體質感
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            draw.text((x3 + dx, start_y + dy), lines[2], font=font_line3, fill="#FFFFFF")
            
    # 正色填滿
    draw.text((x3, start_y), lines[2], font=font_line3, fill=colors[2])


def apply_third_line_skew_distortion(image_path):
    """ 
    針對整張圖進行整體的隨機變形，同時會讓第三行可愛字體
    產生自帶手寫感的俏皮傾斜，天天都不一樣！
    """
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        x_scale = random.uniform(0.96, 1.04)   # 天天自動微調胖瘦
        y_scale = random.uniform(0.98, 1.02)
        x_shear = random.uniform(-0.06, -0.02) # 固定帶有一點活潑的左傾斜
        y_shear = random.uniform(-0.01, 0.01)
        
        img = img.transform(
            (width, height),
            Image.Transform.AFFINE,
            (x_scale, x_shear, 0, y_shear, y_scale, 0),
            resample=Image.Resampling.BILINEAR
        )
        img.save(image_path, "JPEG", quality=95)
    except Exception as e:
        print(f"視覺隨機變形略過: {e}")

def generate_morning_image(text_content):
    """ 隨機獲取背景圖片庫 """
    pic_ids = [10, 28, 48, 54, 116, 192, 230, 235, 327, 404, 343, 364, 411, 444, 486, 522, 532, 593, 619, 650]
    bg_url = f"https://picsum.photos/id/{random.choice(pic_ids)}/800/600"
    
    try:
        img_res = requests.get(bg_url, timeout=15, stream=True)
        if img_res.status_code != 200:
            fallback_url = "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?q=80&w=800"
            img_res = requests.get(fallback_url, timeout=10, stream=True)
            
        img = Image.open(img_res.raw).convert("RGB")
        img = img.resize((800, 600))
        img = img.filter(ImageFilter.GaussianBlur(radius=0.6)) # 輕微柔焦
        
        draw = ImageDraw.Draw(img)
        draw_beautiful_text(draw, text_content, 800)
        img.save(LOCAL_IMAGE_PATH, "JPEG", quality=95)
        
        # 進行最後的俏皮傾斜扭曲
        apply_third_line_skew_distortion(LOCAL_IMAGE_PATH)
        return True
    except Exception as e:
        print(f"圖片生成錯誤: {e}")
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
        return f"【成功】三行俏皮可愛版早安圖已發送！內容：{ai_quote}"
    else:
        return f"LINE 發送失敗: {line_res.status_code}"

@app.route("/")
def home():
    return "Gemini 3-Line Cute Style Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
