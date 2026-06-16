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

# 字畫合一主題庫
THEMES = [
    {
        "style": "充滿元氣的暖心太陽",
        "keywords": "日出、朝霞、陽光、藍天",
        "pic_ids": [1062, 1015, 1043, 404, 532, 593, 619, 650]
    },
    {
        "style": "熱情洋溢的森林小熊與大自然",
        "keywords": "森林、綠色大自然、可愛樹木",
        "pic_ids": [10, 28, 48, 54, 116, 192, 230, 327]
    },
    {
        "style": "暖心又悠閒的晨光咖啡",
        "keywords": "早餐、熱咖啡、溫暖的晨光、文青咖啡廳",
        "pic_ids": [63, 225, 365, 431, 765, 996, 1060]
    },
    {
        "style": "漫步在美麗花園的晨光精靈",
        "keywords": "盛開的花朵、美麗花園、春天氣息",
        "pic_ids": [152, 235, 343, 364, 411, 444, 486, 522]
    }
]

# 保底罐頭文案
BACKUP_QUOTES = [
    "大家早安，元氣滿滿，記得吃早餐喔",
    "早安新一天，快樂劈里啪啦，幸福向你狂奔",
    "大家早安，保持微笑，今天也要超級快樂"
]

COLOR_PALETTES = [
    ("#FFFFFF", "#FFD700", "#FFD700", "#FFFF00"),
    ("#FFFFFF", "#FF69B4", "#FFC0CB", "#FF1493"),
    ("#FFFFFF", "#FF4500", "#FFA500", "#FFD700"),
    ("#FFFFFF", "#00FF7F", "#ADFF2F", "#00FFFF"),
    ("#FFFF00", "#FFFFFF", "#FFFFFF", "#FF69B4")
]

def get_gemini_morning_quote(selected_theme):
    """ 透過高隨機度參數與嚴格指令，確保每次生成的早安句子絕對不重複、且字數安全 """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return random.choice(BACKUP_QUOTES)
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [{
            "parts": [{
                "text": (
                    f"你是一位說話風格極度『俏皮、可愛、活潑、幽默』的早安圖文學大師。\n"
                    f"今天這張早安圖的背景畫面是：【{selected_theme['keywords']}】。\n"
                    f"請你配合這個背景，以『{selected_theme['style']}』的語氣，全新創作一句送給好友的早安問候語。必須遵守以下鐵律：\n"
                    "1. 【絕對不重複】：每次想的句子都要有全新的創意，文字必須和背景畫面完美呼應、絕不突兀！\n"
                    "2. 【嚴格字數限制】：總字數必須控制在 15 到 18 個字之間！絕對不能超過 18 個字！\n"
                    "3. 內容中間必須包含兩個全形逗號『，』，將整句話自然分成『三段』。\n"
                    "   第一段是早安開頭（例如：大家早安），第二段是活力描述，第三段是可愛結尾。\n"
                    "   【重點】第一段（第一個逗號前）字數請嚴格控制在 4 到 5 個字，絕對不能多！\n"
                    "4. 絕對不要有任何驚嘆號、句號等標點符號（只要那兩個全形逗號），不要任何 Emoji 貼圖。只要純中文字。"
                )
            }]
        }],
        "generationConfig": {
            "temperature": 1.0
        }
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            result = res.json()
            quote = result['candidates'][0]['content']['parts'][0]['text'].strip()
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

def draw_beautiful_text(base_img, text):
    """ 改良版製圖：基礎圖層與文字合併處理，加入第三行隨機手寫歪斜效果 """
    image_width, image_height = base_img.size
    draw = ImageDraw.Draw(base_img)

    if "，" in text:
        lines = [line.strip() for line in text.split("，") if line.strip()]
    else:
        third = len(text) // 3
        lines = [text[:third], text[third:third*2], text[third*2:]]

    while len(lines) < 3:
        lines.append("今天也要超級快樂")

    # 恢復大氣的 55 號標題字型
    font_line1 = get_must_font(55)
    font_line2 = get_must_font(38)
    font_line3 = get_must_font(42)

    color1, color2, color3, color_special = random.choice(COLOR_PALETTES)
    colors = [color1, color2, color_special]

    line_heights = [int(55 * 1.4), int(38 * 1.4), int(42 * 1.5)]
    total_height = sum(line_heights) + 40
    start_y = 440 - (total_height // 2)

    # 第一行
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

    # 【升級：第三行微歪斜手寫感，絕不漏黑邊、不切字】
    try: w3 = draw.textlength(lines[2], font=font_line3)
    except: w3 = len(lines[2]) * 42
    h3 = line_heights[2]

    # 建立一個足夠寬、透明的文字專用畫布（前後留白防止旋轉切字）
    pad_w = w3 + 100
    pad_h = h3 + 60
    txt_img = Image.new("RGBA", (int(pad_w), int(pad_h)), (0, 0, 0, 0))
    txt_draw = ImageDraw.Draw(txt_img)

    # 在透明畫布的正中央繪製文字與粗黑邊
    tx = 50
    ty = 30
    for dx in range(-5, 6):
        for dy in range(-5, 6):
            if abs(dx) + abs(dy) <= 8:
                txt_draw.text((tx + dx, ty + dy), lines[2], font=font_line3, fill="black")
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            txt_draw.text((tx + dx, ty + dy), lines[2], font=font_line3, fill="#FFFFFF")
    txt_draw.text((tx, ty), lines[2], font=font_line3, fill=colors[2])

    # 隨機抽取 -2.0 到 +2.0 之間的微小歪斜角度
    skew_angle = random.uniform(-2.0, 2.0)
    rotated_txt = txt_img.rotate(skew_angle, resample=Image.BICUBIC, expand=True)

    # 計算貼回大圖時的中央坐標
    final_w, final_h = rotated_txt.size
    paste_x = (image_width - final_w) // 2
    paste_y = start_y - (final_h - h3) // 2

    # 將微歪斜的文字層完美融合到底圖上
    base_img.paste(rotated_txt, (int(paste_x), int(paste_y)), rotated_txt)


def generate_morning_image(text_content, selected_theme):
    chosen_id = random.choice(selected_theme["pic_ids"])
    bg_url = f"https://picsum.photos/id/{chosen_id}/800/600"
    
    try:
        img_res = requests.get(bg_url, timeout=15, stream=True)
        if img_res.status_code != 200:
            fallback_url = "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?q=80&w=800"
            img_res = requests.get(fallback_url, timeout=10, stream=True)
            
        img = Image.open(img_res.raw).convert("RGB")
        img = img.resize((800, 600))
        img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
        
        # 呼叫改良後的繪圖函數
        draw_beautiful_text(img, text_content)
        
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

        today_theme = random.choice(THEMES)
        ai_quote = get_gemini_morning_quote(today_theme)

        if not generate_morning_image(ai_quote, today_theme):
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
        
        if line_res.status_code == 200:
            return "OK"
        else:
            return f"Error:LINE {line_res.status_code}"
            
    finally:
        IS_PROCESSING = False

@app.route("/")
def home():
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
