import os
import time
import random
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = Flask(__name__)

# 使用全局變數紀錄當前最新的檔案名稱
CURRENT_IMAGE_NAME = "morning_base.jpg"
FONT_FILE_NAME = "morning.ttf"

# 全局鎖，防止重複觸發
IS_PROCESSING = False
LAST_COLOR_INDEX = -1

THEMES = [
    {"style": "充滿元氣、陽光朝氣"},
    {"style": "溫馨療癒、幸福滿滿"},
    {"style": "文青優雅、悠閒晨光"},
    {"style": "清新自然、平安愉快"}
]

BACKUP_QUOTES = [
    "早安新一天，快樂劈里啪啦，幸福向你狂奔",
    "大家早安，保持微笑，今天也要超級快樂",
    "清晨好問候，元氣滿滿，記得吃份溫暖早餐",
    "好朋友早安，把煩惱拋開，迎接幸運的一天",
    "祝您早安，平安愉快，天天都有好心情喔"
]

COLOR_PALETTES = [
    ("#FFF700", "#FFFFFF", "#FF69B4"), # 1. 亮麗黃 ＋ 純白 ＋ 亮粉紅
    ("#FFFFFF", "#FF4500", "#FFF700"), # 2. 純白 ＋ 活力橘 ＋ 鮮明黃
    ("#FF69B4", "#FFFFFF", "#FFFDD0"), # 3. 亮粉紅 ＋ 純白 ＋ 奶油黃
    ("#FFFDD0", "#00FF7F", "#FFFFFF"), # 4. 奶油黃 ＋ 草本綠 ＋ 純白
    ("#00BFFF", "#FFFFFF", "#FFF700"), # 5. 天空藍 ＋ 純白 ＋ 檸檬黃
    ("#FFFFFF", "#E1AD01", "#FF69B4"), # 6. 純白 ＋ 芥末黃 ＋ 優雅粉
    ("#FF4500", "#FFFFFF", "#00FF7F"), # 7. 奔放橘 ＋ 純白 ＋ 清新綠
    ("#FFFF33", "#FF1493", "#FFFFFF"), # 8. 閃亮黃 ＋ 深粉紅 ＋ 純白
    ("#FFFFFF", "#00CED1", "#FFA500"), # 9. 純白 ＋ 湖水藍 ＋ 溫暖橘
    ("#FF6347", "#FFFF00", "#FFFFFF"), # 10. 番茄紅 ＋ 閃亮黃 ＋ 純白
    ("#00FF7F", "#FFFFFF", "#FF4500"), # 11. 草本綠 ＋ 純白 ＋ 活力橘
    ("#FFFF00", "#FF69B4", "#FFFFFF")  # 12. 金黃色 ＋ 少女粉 ＋ 純白
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
                    f"你是一位說話風格極度『俏皮、可愛、活潑、幽默』的早安圖問候語大師。\n"
                    f"請發揮你的最高創意，以『{selected_theme['style']}』的溫暖語氣，創作用於早安圖的問候語。必須遵守以下鐵律：\n"
                    "1. 【嚴格字數限制】：總字數必須控制在 25 到 32 個字之間！\n"
                    "2. 內容中間必須包含兩個全形逗號『，』，將整句話自然分成『三段』。\n"
                    "3. 【最重要鐵律-第一段規範】：第一段是標題開頭（必須包含早安），字數嚴格限制在 4 到 10 個字以內。\n"
                    "   第一段必須使用台灣最親切自然的常用問候語開頭（例如：大家早安、好友早安、親愛的朋友早安、祝您早安、早安你好）。\n"
                    "   【死命令】：絕對不准自己發明奇怪、不合常理的詞彙（例如絕對不准出現綠林早安、相機早安、咖啡早安、朝霞早安等怪詞）！\n"
                    "4. 絕對不要任何驚嘆號、句號等標點符號（只要那兩個全形逗號），不要任何 Emoji 貼圖。只要純中文字。"
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

    shadow_radius = 7 if is_title else 5
    for dx in range(-shadow_radius, shadow_radius + 1):
        for dy in range(-shadow_radius, shadow_radius + 1):
            if abs(dx) + abs(dy) <= shadow_radius:
                txt_draw.text((tx + dx, ty + dy), text, font=font, fill="black")
                
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

    font_line1 = get_must_font(60)
    font_line2 = get_must_font(36)
    font_line3 = get_must_font(38)

    available_indices = [i for i in range(len(COLOR_PALETTES)) if i != LAST_COLOR_INDEX]
    chosen_index = random.choice(available_indices)
    LAST_COLOR_INDEX = chosen_index
    
    color1, color2, color3 = COLOR_PALETTES[chosen_index]

    draw_single_skew_line(base_img, lines[0], font_line1, color1, 340, image_width, is_title=True)
    draw_single_skew_line(base_img, lines[1], font_line2, color2, 435, image_width, is_title=False)
    draw_single_skew_line(base_img, lines[2], font_line3, color3, 525, image_width, is_title=False)


def generate_morning_image(text_content):
    global CURRENT_IMAGE_NAME
    chosen_id = random.randint(100, 500)
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
        
        # 清理舊的隨機命名圖片檔案，避免佔用伺服器硬碟空間
        if CURRENT_IMAGE_NAME and os.path.exists(CURRENT_IMAGE_NAME) and CURRENT_IMAGE_NAME != "morning_base.jpg":
            try:
                os.remove(CURRENT_IMAGE_NAME)
            except:
                pass

        # 【核心修正】每次儲存都附帶當前秒數，徹底改變實體檔案路徑
        new_filename = f"morning_output_{int(time.time())}.jpg"
        img.save(new_filename, "JPEG", quality=95)
        CURRENT_IMAGE_NAME = new_filename
        return True
    except Exception as e:
        print(f"圖片生成錯誤: {e}")
        return False

@app.route("/get_image/<filename>")
def serve_image(filename):
    # 透過動態路徑獲取實體圖片
    if os.path.exists(filename):
        res = send_file(filename, mimetype="image/jpeg")
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
        
        # 生成新圖並更新當前最新的檔名
        generate_morning_image(ai_quote)
            
        # 【核心修正】網址後面加上兩層隨機變數，逼迫 LINE 的伺服器重新抓取全新內容
        rand_num = random.randint(10000, 99999)
        final_image_url = f"{RENDER_EXTERNAL_URL.rstrip('/')}/get_image/{CURRENT_IMAGE_NAME}?rand={rand_num}"

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
