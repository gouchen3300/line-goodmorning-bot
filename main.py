import os
import time
import random
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = Flask(__name__)

LOCAL_IMAGE_PATH = "morning_output.jpg"
FONT_FILE_NAME = "morning.ttf"

IS_PROCESSING = False

# 全局變數：紀錄上一次使用的調色盤索引，防止連續顏色重複
LAST_COLOR_INDEX = -1

THEMES = [
    {
        "style": "充滿元氣的暖心太陽",
        "keywords": "日出、朝霞、陽光、藍天、日落",
        "pic_ids": list(range(100, 200))
    },
    {
        "style": "熱情洋溢的森林小熊與大自然",
        "keywords": "茂密森林、綠色植物、可愛大樹、山巒",
        "pic_ids": list(range(200, 300))
    },
    {
        "style": "暖心又悠閒的晨光咖啡",
        "keywords": "熱咖啡、溫暖晨光、文青咖啡廳、精緻早餐",
        "pic_ids": list(range(300, 400))
    },
    {
        "style": "漫步在美麗花園的晨光精靈",
        "keywords": "盛開的花朵、美麗花園、春天景緻",
        "pic_ids": list(range(400, 500))
    }
]

BACKUP_QUOTES = [
    "早安新一天，快樂劈里啪啦，幸福向你狂奔",
    "大家早安，保持微笑，今天也要超級快樂",
    "清晨好問候，元氣滿滿，記得吃份溫暖早餐",
    "好朋友早安，把煩惱拋開，迎接幸運的一天",
    "祝您早安，平安愉快，天天都有好心情喔"
]

# 【大升級】精心調配的 12 組多色系調色盤（每組格式：第一行字色, 第二行字色, 第三行字色, 備用特殊色）
COLOR_PALETTES = [
    # ─── 黃色系三種層次 ───
    ("#FFFFFF", "#FFF700", "#FFF700", "#FFFF33"), # 1. 鮮明檸檬黃（朝氣陽光）
    ("#FFFFFF", "#FFFDD0", "#FFFDD0", "#FDF5E6"), # 2. 溫柔奶油黃（軟萌療癒）
    ("#FFFFFF", "#E1AD01", "#E1AD01", "#FFC125"), # 3. 質感芥末黃（文青復古）
    
    # ─── 粉紅系兩種層次 ───
    ("#FFFFFF", "#FF69B4", "#FFC0CB", "#FF1493"), # 4. 少女亮粉紅（活潑可愛）
    ("#FFFFFF", "#C71585", "#DB7093", "#FF69B4"), # 5. 優雅玫瑰粉（成熟高雅）
    
    # ─── 橘紅系兩種層次 ───
    ("#FFFFFF", "#FF4500", "#FFA500", "#FFD700"), # 6. 奔放活力橘（元氣滿滿）
    ("#FFFFFF", "#FF6347", "#FF7F50", "#FF4500"), # 7. 溫暖番茄紅（亮麗吸睛）
    
    # ─── 綠色系兩種層次 ───
    ("#FFFFFF", "#00FF7F", "#ADFF2F", "#00FFFF"), # 8. 清新草本綠（大自然風）
    ("#FFFFFF", "#228B22", "#32CD32", "#00FF00"), # 9. 森林翡翠綠（沉穩茂密）
    
    # ─── 藍色系兩種層次 ───
    ("#FFFFFF", "#00BFFF", "#87CEFA", "#1E90FF"), # 10. 湛藍蔚藍天（遼闊晴空）
    ("#FFFFFF", "#00CED1", "#20B2AA", "#40E0D0"), # 11. 夢幻湖水綠藍/Tiffany藍
    
    # ─── 經典高對比撞色 ───
    ("#FFFF00", "#FFFFFF", "#FFFFFF", "#FF69B4")  # 12. 閃亮黃配純白（長輩最愛亮眼款）
]

def get_gemini_morning_quote(selected_theme):
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
                    "1. 【60天絕不重複】：發揮你的最高創意，文字必須和背景畫面完美呼應、絕不突兀！\n"
                    "2. 【嚴格字數限制】：總字數必須控制在 25 到 32 個字之間！\n"
                    "3. 內容中間必須包含兩個全形逗號『，』，將整句話自然分成『三段』。\n"
                    "   【最重要鐵律】第一段是標題開頭（必須包含早安），字數請『嚴格限制在 4 到 10 個字以內』，絕對不能多於 10 個字！\n"
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

def draw_single_skew_line(base_img, text, font, color, center_y, image_width, is_title=False):
    try:
        text_w = ImageDraw.Draw(base_img).textlength(text, font=font)
    except:
        text_w = len(text) * font.size
    text_h = int(font.size * 1.2)

    pad = 40
    txt_w = int(text_w + pad * 2)
    txt_h = int(text_h + pad * 2)
    
    txt_img = Image.new("RGBA", (txt_w, txt_h), (0, 0, 0, 0))
    txt_draw = ImageDraw.Draw(txt_img)

    tx = pad
    ty = pad

    # 經典立體厚黑邊外框
    shadow_radius = 7 if is_title else 5
    for dx in range(-shadow_radius, shadow_radius + 1):
        for dy in range(-shadow_radius, shadow_radius + 1):
            if abs(dx) + abs(dy) <= shadow_radius:
                txt_draw.text((tx + dx, ty + dy), text, font=font, fill="black")
                
    # 內襯白邊，讓色彩層次更跳脫
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            txt_draw.text((tx + dx, ty + dy), text, font=font, fill="#FFFFFF")
            
    txt_draw.text((tx, ty), text, font=font, fill=color)

    if is_title:
        skew_angle = 0.0
    else:
        direction = random.choice([-1, 1])
        skew_angle = direction * random.uniform(6.0, 11.0)

    rotated_txt = txt_img.rotate(skew_angle, resample=Image.BICUBIC, expand=True)

    r_w, r_h = rotated_txt.size
    paste_x = (image_width - r_w) // 2
    paste_y = center_y - (r_h // 2)

    base_img.paste(rotated_txt, (int(paste_x), int(paste_y)), rotated_txt)

def draw_beautiful_text(base_img, text):
    global LAST_COLOR_INDEX
    image_width, image_height = base_img.size

    if "，" in text:
        lines = [line.strip() for line in text.split("，") if line.strip()]
    else:
        third = len(text) // 3
        lines = [text[:third], text[third:third*2], text[third*2:]]

    while len(lines) < 3:
        lines.append("今天也要超級快樂")

    # 標題維持霸氣 60 號字
    font_line1 = get_must_font(60)
    font_line2 = get_must_font(36)
    font_line3 = get_must_font(38)

    # 從 12 組色系中抽取，且保證不與昨天重複
    available_indices = [i for i in range(len(COLOR_PALETTES)) if i != LAST_COLOR_INDEX]
    chosen_index = random.choice(available_indices)
    LAST_COLOR_INDEX = chosen_index
    
    color1, color2, color3, color_special = COLOR_PALETTES[chosen_index]
    colors = [color1, color2, color_special]

    # 黃金置中排版
    draw_single_skew_line(base_img, lines[0], font_line1, colors[0], 340, image_width, is_title=True)
    draw_single_skew_line(base_img, lines[1], font_line2, colors[1], 435, image_width, is_title=False)
    draw_single_skew_line(base_img, lines[2], font_line3, colors[2], 525, image_width, is_title=False)


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
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        
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
        return "OK"
        
    IS_PROCESSING = True
    
    try:
        LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
        LINE_USER_ID = os.environ.get("LINE_USER_ID")
        RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
        
        if not all([LINE_ACCESS_TOKEN, LINE_USER_ID]):
            return "OK"
            
        if not RENDER_EXTERNAL_URL:
            RENDER_EXTERNAL_URL = "https://" + requests.headers.get('Host', '')

        today_theme = random.choice(THEMES)
        ai_quote = get_gemini_morning_quote(today_theme)
        generate_morning_image(ai_quote, today_theme)
            
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
        
        requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload, timeout=15)
        return "OK"
        
    except Exception as e:
        print(f"觸發程序發生異常: {e}")
        return "OK"
    finally:
        IS_PROCESSING = False

@app.route("/")
def home():
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
