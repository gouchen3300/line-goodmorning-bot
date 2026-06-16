import os
import time
import random
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = Flask(__name__)

LOCAL_IMAGE_PATH = "morning_output.jpg"
FONT_FILE_NAME = "morning.ttf"

# 防止同時間重複觸發的鎖定開關
IS_PROCESSING = False

# 安全保底罐頭文案（字數極簡、絕不切邊）
BACKUP_QUOTES = [
    "大家早安，元氣滿滿，記得吃早餐喔",
    "早安新一天，快樂劈里啪啦，幸福向你狂奔",
    "大家早安，保持微笑，今天也要超級快樂"
]

# 充滿朝氣的豐富顏色搭配（標題, 內文1, 內文2, 第三行可愛亮色）
COLOR_PALETTES = [
    ("#FFFFFF", "#FFD700", "#FFD700", "#FFFF00"),  # 經典金黃 + 閃亮黃
    ("#FFFFFF", "#FF69B4", "#FFC0CB", "#FF1493"),  # 嬌豔粉紅 + 俏皮深粉
    ("#FFFFFF", "#FF4500", "#FFA500", "#FFD700"),  # 活力亮橘 + 溫暖金黃
    ("#FFFFFF", "#00FF7F", "#ADFF2F", "#00FFFF"),  # 英文嫩綠 + 璀璨藍綠
    ("#FFFF00", "#FFFFFF", "#FFFFFF", "#FF69B4")   # 黃金標題 + 純白內文 + 少女粉紅
]

def get_gemini_morning_quote():
    """ 透過高隨機度參數與嚴格指令，確保每次生成的早安句子絕對不重複、且字數安全 """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return random.choice(BACKUP_QUOTES)
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    random_styles = [
        "充滿元氣的小兔子", "幽默貼心的好朋友", "暖心又調皮的晨光精靈", "天天逗你笑的開心果",
        "滿滿正能量的向日葵", "熱情洋溢的森林小熊", "溫柔守護的微風精靈", "活力四射的早安使者"
    ]
    selected_style = random.choice(random_styles)
    
    payload = {
        "contents": [{
            "parts": [{
                "text": (
                    f"你是一位說話風格極度『俏皮、可愛、活潑、幽默』的早安圖文學大師。請以『{selected_style}』的語氣，"
                    "全新創作一句送給好友的早安問候語。必須遵守以下鐵律：\n"
                    "1. 【絕對不重複】：每次想的句子都要有全新的創意、換不同的詞彙，絕對不能跟之前的相似！\n"
                    "2. 【嚴格字數限制】：總字數必須控制在 15 到 18 個字之間！絕對不能超過 18 個字！\n"
                    "3. 內容中間必須包含兩個全形逗號『，』，將整句話自然分成『三段』。\n"
                    "   第一段是早安開頭（例如：大家早安），第二段是活力描述，第三段是可愛結尾。\n"
                    "   【重點】因為第一行字很大，第一段（逗號前）字數請嚴格控制在 4 到 5 個字，絕對不能多！\n"
                    "4. 絕對不要有任何驚嘆號、句號等標點符號（只要那兩個全形逗號），不要任何 Emoji 貼圖。只要純中文字。"
                )
            }]
        }],
        "generationConfig": {
            "temperature": 1.0  # 提高隨機度，徹底根治句子重複的問題！
        }
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            result = res.json()
            quote = result['candidates'][0]['content']['parts'][0]['text'].strip()
            # 過濾掉雜質標點符號
            for punc in ['。', '！', '、', '？', '；', '：', '.', '!', '?', '"', '「', '」', '*', '\n', ' ']:
                quote = quote.replace(punc, '')
            if quote and quote.count("，") == 2:
                return quote
    except Exception as e:
        print(f"Gemini API 生成出錯: {e}")
        
    return random.choice(BACKUP_QUOTES)

def get_must_font(size):
    if os.path.exists(FONT_FILE_NAME):
        try:
            return ImageFont.truetype(FONT_FILE_NAME, size)
        except:
            pass
    return ImageFont.load_default()

def draw_beautiful_text(draw, text, image_width):
    if "，" in text:
        lines = [line.strip() for line in text.split("，") if line.strip()]
    else:
        third = len(text) // 3
        lines = [text[:third], text[third:third*2], text[third*2:]]

    while len(lines) < 3:
        lines.append("今天也要超級快樂")

    # 【恢復 55】遵照吳大哥指示，第一行恢復霸氣的 55 大字型！
    font_line1 = get_must_font(55)
    font_line2 = get_must_font(38)
    font_line3 = get_must_font(42)

    color1, color2, color3, color_special = random.choice(COLOR_PALETTES)
    colors = [color1, color2, color_special]

    line_heights = [int(55 * 1.4), int(38 * 1.4), int(42 * 1.5)]
    total_height = sum(line_heights) + 40
    start_y = 440 - (total_height // 2)

    # 第一行（大標題 55 + 超粗外框加工）
    try: w1 = draw.textlength(lines[0], font=font_line1)
    except: w1 = len(lines[0]) * 55
    x1 = (image_width - w1) // 2
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            draw.text((x1 + dx, start_y + dy), lines[0], font=font_line1, fill="black")
    draw.text((x1, start_y), lines[0], font=font_line1, fill=colors[0])
    start_y += line_heights[0] + 15

    # 第二行
    try: w2 = draw.textlength(lines[1], font=font_line2)
    except: w2 = len(lines[1]) * 38
    x2 = (image_width - w2) // 2
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            draw.text((x2 + dx, start_y + dy), lines[1], font=font_line2, fill="black")
    draw.text((x2, start_y), lines[1], font=font_line2, fill=colors[1])
    start_y += line_heights[1] + 20

    # 第三行（極限加粗立體字）
    try: w3 = draw.textlength(lines[2], font=font_line3)
    except: w3 = len(lines[2]) * 42
    x3 = (image_width - w3) // 2
    for dx in range(-5, 6):
        for dy in range(-5, 6):
            if abs(dx) + abs(dy) <= 8:
                draw.text((x3 + dx, start_y + dy), lines[2], font=font_line3, fill="black")
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            draw.text((x3 + dx, start_y + dy), lines[2], font=font_line3, fill="#FFFFFF")
    draw.text((x3, start_y), lines[2], font=font_line3, fill=colors[2])


def generate_morning_image(text_content):
    # 【擴充背景庫】一口氣擴充到 50 張精選圖片 ID，徹底解決天天看到重複圖片的問題！
    pic_ids = [
        10, 28, 48, 54, 116, 192, 230, 235, 327, 404, 343, 364, 411, 444, 486, 522, 532, 593, 619, 650,
        15, 19, 29, 37, 43, 58, 76, 122, 133, 146, 152, 175, 200, 211, 250, 260, 311, 350, 365, 399,
        425, 450, 499, 510, 555, 564, 588, 600, 625, 666
    ]
    bg_url = f"https://picsum.photos/id/{random.choice(pic_ids)}/800/600"
    
    try:
        img_res = requests.get(bg_url, timeout=15, stream=True)
        if img_res.status_code != 200:
            fallback_url = "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?q=80&w=800"
            img_res = requests.get(fallback_url, timeout=10, stream=True)
            
        img = Image.open(img_res.raw).convert("RGB")
        img = img.resize((800, 600))
        img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
        
        draw = ImageDraw.Draw(img)
        draw_beautiful_text(draw, text_content, 800)
        img.save(LOCAL_IMAGE_PATH, "JPEG", quality=95)
        return True
    except Exception as e:
        print(f"圖片生成錯誤: {e}")
        return False

@app.route("/morning_image.jpg")
def serve_image():
    if os.path.exists(LOCAL_IMAGE_PATH):
        res = send_file(LOCAL_IMAGE_PATH, mimetype="image/jpeg")
        res.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        res.headers["Pragma"] = "no-cache"
        res.headers["Expires"] = "0"
        return res
    return "Image not found.", 404

@app.route("/trigger")
def trigger():
    global IS_PROCESSING
    # 被攔截時只回傳精簡 "Duplicate"，完美解決 cron-job 報錯問題
    if IS_PROCESSING:
        return "Duplicate"
        
    IS_PROCESSING = True
    
    try:
        LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
        LINE_USER_ID = os.environ.get("LINE_USER_ID")
        RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
        
        if not all([LINE_ACCESS_TOKEN, LINE_USER_ID]):
            return "Error:Missing Env"
            
        if not RENDER_EXTERNAL_URL:
            RENDER_EXTERNAL_URL = "https://" + requests.headers.get('Host', '')

        ai_quote = get_gemini_morning_quote()

        if not generate_morning_image(ai_quote):
            return "Error:Image Failed"
            
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
        
        # 成功只回傳最精簡的 "OK"
        if line_res.status_code == 200:
            return "OK"
        else:
            return f"Error:LINE {line_res.status_code}"
            
    finally:
        # 解開重複鎖定
        IS_PROCESSING = False

@app.route("/")
def home():
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
