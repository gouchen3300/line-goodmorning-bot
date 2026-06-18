import os
import time
import random
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = Flask(__name__)

# 修復：回歸固定檔名，避免檔案因 Render 重置而消失
LOCAL_IMAGE_PATH = "morning_output.jpg"
FONT_FILE_NAME = "morning.ttf"

# 防止重複觸發的鎖
IS_PROCESSING = False
LAST_COLOR_INDEX = -1

# 清除具體關鍵字，採用全方位正能量風格主題
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

# 精選 12 組強烈撞色對比色調色盤
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
                    "1. 【嚴格字數限制】：總字數控制在 25 到 32 個字之間！\n"
                    "2. 內容中間由兩個全形逗號『，』自然分成『三段』。\n"
                    "3. 【最重要鐵律-第一段】：第一段是標題開頭（必須含早安），字數嚴格限制在 4 到 10 字以內。\n"
                    "   第一段必須使用台灣自然常見的問候語開頭（例如：大家早安、好友早安、親愛的朋友早安、早安你好）。"
                    "   【死命令】：不准生造怪詞（例如絕對不准出現綠林早安、相機早安、咖啡早安）！\n"
                    "4. 不要任何驚嘆號、句號等標點符號，不要任何 Emoji 貼圖。只要純中文字。"
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
    """ 大角度整行歪斜，置中大字 """
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

    # 經典超厚黑邊（7像素/5像素）
    shadow_radius = 7 if is_title else 5
    for dx in range(-shadow_radius, shadow_radius + 1):
        for dy in range(-shadow_radius, shadow_radius + 1):
            if abs(dx) + abs(dy) <= shadow_radius:
                txt_draw.text((tx + dx, ty + dy), text, font=font, fill="black")
                
    # 內襯白邊
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            txt_draw.text((tx + dx, ty + dy), text, font=font, fill="#FFFFFF")
            
    txt_draw.text((tx, ty), text, font=font, fill=color)

    if is_title:
        skew_angle = 0.0
    else:
        # 大角度歪斜 -11 ~ -6 或 6 ~ 11
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

    # 防重複調色盤機制
    available_indices = [i for i in range(len(COLOR_PALETTES)) if i != LAST_COLOR_INDEX]
    chosen_index = random.choice(available_indices)
    LAST_COLOR_INDEX = chosen_index
    
    color1, color2, color3 = COLOR_PALETTES[chosen_index]

    # 置中排版
    draw_single_skew_line(base_img, lines[0], font_line1, color1, 340, image_width, is_title=True)
    draw_single_skew_line(base_img, lines[1], font_line2, color2, 435, image_width, is_title=False)
    draw_single_skew_line(base_img, lines[2], font_line3, color3, 525, image_width, is_title=False)


def generate_morning_image(text_content):
    # 隨機抓大自然風景圖
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
        # 修復：儲存至固定檔名，避免重置後檔案消失
        img.save(LOCAL_IMAGE_PATH, "JPEG", quality=95)
        return True
    except Exception as e:
        print(f"圖片生成錯誤: {e}")
        return False

@app.route("/morning_image.jpg")
def serve_image():
    # 修復：提供固定檔名的圖片服務
    if os.path.exists(LOCAL_IMAGE_PATH):
        res = send_file(LOCAL_IMAGE_PATH, mimetype="image/jpeg")
        # 核心修復：強制加上 HTTP Header，徹底告訴 LINE：不要暫存我！
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
        
        if not generate_morning_image(ai_quote):
            return "OK"
            
        # 修復：網址回歸固定路徑，只加微小時間戳記
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
        # 核心修復：極簡回報，徹底解決 cron 認為 output large 的問題
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
