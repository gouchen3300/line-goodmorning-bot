import os
import time
import random
import threading
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = Flask(__name__)

LOCAL_IMAGE_PATH = "morning_output.jpg"
FONT_FILE_NAME = "morning.ttf"

# 🌟 改用 Threading Lock 確保非同步安全
PROCESS_LOCK = threading.Lock()
IS_PROCESSING = False

LAST_TRIGGER_HOUR = ""
LAST_AI_TEXT = ""
CURRENT_INDEX = 0

FESTIVALS = {
    "01-01": {
        "text": "元旦快樂，新的一年，祝您百事可樂，萬事如意", 
        "keywords": ["fireworks", "new-year-celebration", "sunrise"],
        "colors": ("#FF1493", "#FFFFFF", "#FFFF00")
    },
    "01-28": {
        "text": "恭賀新禧，新春飛揚，祝您闔家團圓，福氣滿滿，萬事如意", 
        "keywords": ["red-lanterns", "chinese-lantern", "chinese-architecture"],
        "colors": ("#FF3333", "#FFFFFF", "#FFFF00")
    },
    "05-10": {
        "text": "母親節快樂，感恩辛苦的媽媽，祝天天開心，平安健康", 
        "keywords": ["carnation", "pink-flowers", "mother-love"],
        "colors": ("#FF69B4", "#FFFFFF", "#FFFDD0")
    },
    "06-19": { # 2026年端午節
        "text": "端午安康，粽香四溢，祝您與家人佳節愉快，闔家安康", 
        "keywords": ["dragonboat", "bamboo-leaves", "river-water", "rowing"],
        "colors": ("#00FF7F", "#FFFFFF", "#FFF700")
    },
    "08-08": {
        "text": "父親節快樂，爸爸您辛苦了，祝您身體健康，萬事順心", 
        "keywords": ["father-and-son", "thank-you-dad", "warm-light"],
        "colors": ("#00BFFF", "#FFFFFF", "#FFF700")
    },
    "09-25": { # 2026年中秋節
        "text": "中秋佳節快樂，月圓人團圓，祝您幸福美滿，事事順心", 
        "keywords": ["full-moon", "moonlight", "night-sky", "lantern"],
        "colors": ("#FFFF33", "#FFFFFF", "#FFA500")
    },
    "12-25": {
        "text": "聖誕佳節平安，迎接溫馨歲末，祝您喜樂滿滿，幸福相隨", 
        "keywords": ["christmas-tree", "snow-warm", "gift-box"],
        "colors": ("#FF4500", "#FFFFFF", "#00FF7F")
    }
}

STATIC_ROUNDS = [
    {"text": "大家早安，保持微笑，今天也要超級快樂", "colors": ("#FFF700", "#FFFFFF", "#FF69B4")},
    {"text": "好友早安，清晨好問候，記得吃份溫暖早餐", "colors": ("#FFFFFF", "#FF4500", "#FFF700")},
    {"text": "親愛的朋友早安，把煩惱拋開，迎接幸運的一天", "colors": ("#FF69B4", "#FFFFFF", "#FFFDD0")},
    {"text": "祝您早安，平安愉快，天天都有好心情喔", "colors": ("#FFFDD0", "#00FF7F", "#FFFFFF")},
    {"text": "早安你好，讓陽光帶走疲憊，迎接美好新起點", "colors": ("#00BFFF", "#FFFFFF", "#FFF700")},
    {"text": "大家早安，新的一天，快樂劈里啪啦向你狂奔", "colors": ("#FFFFFF", "#E1AD01", "#FF69B4")},
    {"text": "好友早安，元氣滿滿，幸福已經在悄悄敲門囉", "colors": ("#FF4500", "#FFFFFF", "#00FF7F")},
    {"text": "祝您早安，微笑常在，心想事成萬事都順心", "colors": ("#FFFF33", "#FF1493", "#FFFFFF")},
    {"text": "親愛的朋友早安，放鬆心情，享受悠閒的晨光序曲", "colors": ("#FFFFFF", "#00CED1", "#FFA500")},
    {"text": "早安你好，滿滿正能量，今天也是幸運滿分的一天", "colors": ("#FFFF00", "#FF69B4", "#FFFFFF")}
]

def get_must_font(size):
    if os.path.exists(FONT_FILE_NAME):
        try: return ImageFont.truetype(FONT_FILE_NAME, size)
        except: pass
    return ImageFont.load_default()

def draw_single_skew_line(base_img, text, font, color, center_y, image_width, is_title=False):
    try: text_w = ImageDraw.Draw(base_img).textlength(text, font=font)
    except: text_w = len(text) * font.size
    text_h = int(font.size * 1.2)
    pad = 40
    txt_img = Image.new("RGBA", (int(text_w + pad * 2), int(text_h + pad * 2)), (0, 0, 0, 0))
    txt_draw = ImageDraw.Draw(txt_img)
    shadow_radius = 7 if is_title else 5
    for dx in range(-shadow_radius, shadow_radius + 1):
        for dy in range(-shadow_radius, shadow_radius + 1):
            if abs(dx) + abs(dy) <= shadow_radius:
                txt_draw.text((pad + dx, pad + dy), text, font=font, fill="black")
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            txt_draw.text((pad + dx, pad + dy), text, font=font, fill="#FFFFFF")
    txt_draw.text((pad, pad), text, font=font, fill=color)
    skew_angle = 0.0 if is_title else -7.5
    rotated_txt = txt_img.rotate(skew_angle, resample=Image.BICUBIC, expand=True)
    r_w, r_h = rotated_txt.size
    base_img.paste(rotated_txt, ((image_width - r_w) // 2, center_y - r_h // 2), rotated_txt)

def get_gemini_quote():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return None
    url = f"https://generatelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
    prompt = "請寫一句充滿台灣在地人情味的長句早安問候語，字數約20字左右，格式必須包含逗號。不要有任何解釋與標點符號。"
    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, json=payload, timeout=8)
        if res.status_code == 200:
            text = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            return text.replace("『", "").replace("』", "").replace('"', '').replace("「", "").replace("」", "")
    except: pass
    return None

def generate_morning_image(text_content, colors, keywords_list=None):
    img_success = False
    img = None
    if keywords_list:
        random.shuffle(keywords_list)
        for kw in keywords_list:
            try:
                bg_url = f"https://source.unsplash.com/featured/800x600/?{kw}"
                img_res = requests.get(bg_url, timeout=4, stream=True)
                if img_res.status_code == 200:
                    from io import BytesIO
                    img = Image.open(BytesIO(img_res.content)).convert("RGB")
                    img_success = True
                    break
            except: continue
    if not img_success:
        try:
            random_bg_id = random.randint(100, 500)
            bg_url = f"https://picsum.photos/id/{random_bg_id}/800/600"
            img_res = requests.get(bg_url, timeout=4, stream=True)
            if img_res.status_code == 200:
                img = Image.open(img_res.raw).convert("RGB")
        except: pass
    if not img:
        img = Image.new("RGB", (800, 600), "#2c3e50")
        
    img = img.resize((800, 600))
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    image_width, _ = img.size

    if "，" in text_content: lines = [line.strip() for line in text_content.split("，") if line.strip()]
    elif "," in text_content: lines = [line.strip() for line in text_content.split(",") if line.strip()]
    else:
        third = len(text_content) // 3
        lines = [text_content[:third], text_content[third:third*2], text_content[third*2:]]
    while len(lines) < 3: lines.append("祝您平安愉快")

    font_line1, font_line2, font_line3 = get_must_font(55), get_must_font(36), get_must_font(38)
    draw_single_skew_line(img, lines[0], font_line1, colors[0], 340, image_width, is_title=True)
    draw_single_skew_line(img, lines[1], font_line2, colors[1], 435, image_width, is_title=False)
    draw_single_skew_line(img, lines[2], font_line3, colors[2], 525, image_width, is_title=False)
    img.save(LOCAL_IMAGE_PATH, "JPEG", quality=95)

def async_task(render_url):
    global IS_PROCESSING, LAST_TRIGGER_HOUR, LAST_AI_TEXT, CURRENT_INDEX
    try:
        LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
        LINE_USER_ID = os.environ.get("LINE_USER_ID")
        if not all([LINE_ACCESS_TOKEN, LINE_USER_ID]): return
            
        current_hour = time.strftime("%Y-%m-%d-%H")
        current_date = time.strftime("%m-%d")
        
        if current_date in FESTIVALS and current_hour != LAST_TRIGGER_HOUR:
            fest_data = FESTIVALS[current_date]
            text_content = fest_data["text"]
            colors = fest_data["colors"]
            keywords_list = fest_data["keywords"]
            LAST_TRIGGER_HOUR = current_hour
        elif current_hour != LAST_TRIGGER_HOUR:
            ai_text = get_gemini_quote()
            if ai_text:
                text_content = ai_text
                LAST_AI_TEXT = ai_text
                colors = random.choice(STATIC_ROUNDS)["colors"]
            else:
                round_data = STATIC_ROUNDS[CURRENT_INDEX]
                text_content = round_data["text"]
                colors = round_data["colors"]
                CURRENT_INDEX = (CURRENT_INDEX + 1) % len(STATIC_ROUNDS)
            keywords_list = None
            LAST_TRIGGER_HOUR = current_hour
        else:
            round_data = STATIC_ROUNDS[CURRENT_INDEX]
            text_content = round_data["text"]
            colors = round_data["colors"]
            CURRENT_INDEX = (CURRENT_INDEX + 1) % len(STATIC_ROUNDS)
            keywords_list = None

        generate_morning_image(text_content, colors, keywords_list)
        
        cache_breaker = random.randint(1000, 9999)
        timestamp = int(time.time())
        final_image_url = f"{render_url.rstrip('/')}/morning_image.jpg?rand={cache_breaker}&t={timestamp}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
        }
        payload = {
            "to": LINE_USER_ID,
            "messages": [{
                "type": "image",
                "originalContentUrl": final_image_url,
                "previewImageUrl": final_image_url
            }]
        }
        requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload, timeout=10)
    except Exception as e: print(f"後台錯誤: {e}")
    finally:
        with PROCESS_LOCK:
            IS_PROCESSING = False

@app.route("/morning_image.jpg")
def serve_image():
    if os.path.exists(LOCAL_IMAGE_PATH):
        res = send_file(LOCAL_IMAGE_PATH, mimetype="image/jpeg")
        res.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return res
    return "NotFound", 404

# 🌟 核心修正：極速秒回 OK，徹底杜絕 Failed (output too large)
@app.route("/trigger")
def trigger():
    global IS_PROCESSING
    with PROCESS_LOCK:
        if IS_PROCESSING:
            return "OK" # 正在處理中，直接秒回 OK
        IS_PROCESSING = True
    
    RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if not RENDER_EXTERNAL_URL:
        RENDER_EXTERNAL_URL = "https://" + requests.headers.get('Host', '')

    # 核心關鍵：立刻丟進背景執行，Flask 馬上切斷連線回傳 "OK" 給排程網站
    threading.Thread(target=async_task, args=(RENDER_EXTERNAL_URL,)).start()
    return "OK"

@app.route("/")
def home():
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
