import os
import time
import random
import threading
import requests
from flask import Flask, send_file
# 導入 ImageEnhance 用來強制把照片變得明亮、鮮豔
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

app = Flask(__name__)

LOCAL_IMAGE_PATH = "morning_output.jpg"
FONT_FILE_NAME = "morning.ttf"

PROCESS_LOCK = threading.Lock()
IS_PROCESSING = False

LAST_TRIGGER_HOUR = ""
LAST_AI_TEXT = ""

# 20則精心翻新、充滿正能量與變化的平日制式保底問候語
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
    {"text": "早安你好，滿滿正能量，今天也是幸運滿分的一天", "colors": ("#FFFF00", "#FF69B4", "#FFFFFF")},
    {"text": "新的一天早安，願舒心的陽光，照亮您前行的每一步", "colors": ("#FFFFFF", "#FF8C00", "#00FF7F")},
    {"text": "早安老友，心中有愛自然溫暖，祝今天事事順心如意", "colors": ("#FF69B4", "#FFFFFF", "#FFFF33")},
    {"text": "大家清晨好，送上一聲真摯問候，願您一整天神采飛揚", "colors": ("#FFFDD0", "#00BFFF", "#FFFFFF")},
    {"text": "溫馨早安，把生活調成喜歡的頻道，今天也要幸福滿滿", "colors": ("#FFFFFF", "#FF1493", "#FFF700")},
    {"text": "好友早安，生活因知足而美麗，願您的微笑像陽光燦爛", "colors": ("#FFF700", "#FFFFFF", "#00CED1")},
    {"text": "早安你好，開啟元氣滿滿的一天，好運與您不期而遇", "colors": ("#00FF7F", "#FFFFFF", "#FF4500")},
    {"text": "祝您早安，健康的身體是最大的財富，佳節與平日皆安康", "colors": ("#FFFFFF", "#E1AD01", "#FFFDD0")},
    {"text": "清晨早安，生活雖然平凡，但每一天都值得我們熱烈期待", "colors": ("#FF4500", "#FFFFFF", "#FFFF33")},
    {"text": "各位早安，善待自己的心情，讓幸福的感覺裝滿今天", "colors": ("#FFFF00", "#FF69B4", "#FFFFFF")},
    {"text": "好友早安，最美的風景在路上，最真的問候在每天清晨", "colors": ("#FFFFFF", "#00BFFF", "#FF8C00")}
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
    # 🌟 修正點一：重構並校對最穩定的 Gemini 1.5 Flash API 終端節點與格式
    url = f"https://generatelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    prompt = "請寫一句適合長輩群組、充滿溫馨與正能量的台灣在地早安問候語。字數控制在15到23字之間，中間必須包含一個逗號（，）。嚴禁任何引號、備註、標點符號或解釋，只要這句話本身。"
    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, json=payload, json=payload, timeout=8)
        if res.status_code == 200:
            text = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            # 過濾所有多餘雜質字元
            clean_text = text.replace("『", "").replace("』", "").replace('"', '').replace("「", "").replace("」", "").replace("。", "").replace("*", "")
            if "，" in clean_text or "," in clean_text:
                return clean_text
    except Exception as e:
        print(f"Gemini API 呼叫異常: {e}")
    return None

def generate_morning_image(text_content, colors):
    img = None
    # 🌟 修正點二：捨棄壞掉的舊接口，改用保證高清明亮的精選 Picsum 大自然暖色系圖庫庫存
    bright_ids = [10, 15, 26, 28, 48, 54, 57, 116, 134, 142, 195, 200, 219, 230, 238, 260, 326, 342, 367, 404]
    random.shuffle(bright_ids)
    
    for img_id in bright_ids:
        try:
            bg_url = f"https://picsum.photos/id/{img_id}/800/600"
            img_res = requests.get(bg_url, timeout=5, stream=True)
            if img_res.status_code == 200:
                from io import BytesIO
                img = Image.open(BytesIO(img_res.content)).convert("RGB")
                break
        except: continue

    if not img:
        img = Image.new("RGB", (800, 600), "#FFAD33") # 防線：若斷網，直接使用明亮暖橘色

    img = img.resize((800, 600))
    
    # 🌟 核心修正：強制進行「畫面美化放大鏡」！大幅提升亮度與鮮豔度，杜絕黑白陰暗圖
    enhancer_brightness = ImageEnhance.Brightness(img)
    img = enhancer_brightness.enhance(1.25) # 提高 25% 亮度
    enhancer_color = ImageEnhance.Color(img)
    img = enhancer_color.enhance(1.2) # 提高 20% 色彩鮮豔度
    
    image_width, _ = img.size

    # 切割文字段落
    if "，" in text_content: lines = [line.strip() for line in text_content.split("，") if line.strip()]
    elif "," in text_content: lines = [line.strip() for line in text_content.split(",") if line.strip()]
    else:
        half = len(text_content) // 2
        lines = [text_content[:half], text_content[half:]]
        
    while len(lines) < 3: 
        lines.append("祝您喜樂安康")

    font_line1, font_line2, font_line3 = get_must_font(54), get_must_font(36), get_must_font(38)
    draw_single_skew_line(img, lines[0], font_line1, colors[0], 340, image_width, is_title=True)
    draw_single_skew_line(img, lines[1], font_line2, colors[1], 435, image_width, is_title=False)
    draw_single_skew_line(img, lines[2], font_line3, colors[2], 525, image_width, is_title=False)
    img.save(LOCAL_IMAGE_PATH, "JPEG", quality=95)

def async_task(render_url):
    global IS_PROCESSING, LAST_TRIGGER_HOUR, LAST_AI_TEXT
    try:
        LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
        LINE_USER_ID = os.environ.get("LINE_USER_ID")
        if not all([LINE_ACCESS_TOKEN, LINE_USER_ID]): return
            
        current_hour = time.strftime("%Y-%m-%d-%H")
        
        # 嘗試跟真正修正後的 Gemini API 索取 365 天全新不重複文案
        ai_text = get_gemini_quote()
        if ai_text:
            text_content = ai_text
            LAST_AI_TEXT = ai_text
            colors = random.choice(STATIC_ROUNDS)["colors"]
        else:
            # 🌟 修正點三：萬一 AI 連線出錯，改採隨機抽籤，絕不再死板照順序抓第一則！
            backup_round = random.choice(STATIC_ROUNDS)
            text_content = backup_round["text"]
            colors = backup_round["colors"]

        generate_morning_image(text_content, colors)
        
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
    except Exception as e: 
        print(f"後台處理異常: {e}")
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

@app.route("/trigger")
def trigger():
    global IS_PROCESSING
    with PROCESS_LOCK:
        if IS_PROCESSING:
            return "BUSY"
        IS_PROCESSING = True
    
    RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if not RENDER_EXTERNAL_URL:
        RENDER_EXTERNAL_URL = "https://" + requests.headers.get('Host', '')

    threading.Thread(target=async_task, args=(RENDER_EXTERNAL_URL,)).start()
    return "OK"

@app.route("/")
def home():
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
