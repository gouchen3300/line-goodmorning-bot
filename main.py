import os
import time
import random
import threading
import requests
from flask import Flask, send_file, Response
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO

app = Flask(__name__)

LOCAL_IMAGE_PATH = "morning_output.jpg"
FONT_FILE_NAME = "NotoSansTC-Bold.ttf"
FONT_URL = "https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/TraditionalChinese/NotoSansCJKtc-Bold.otf"

PROCESS_LOCK = threading.Lock()
IS_PROCESSING = False

# 365天備用經典輪播庫（當Gemini API額度用盡或異常時自動補上，確保天天有圖）
STATIC_ROUNDS = [
    {"text": "大家早安，保持微笑，今天也要超級快樂", "colors": ("#FFFF00", "#FFFFFF", "#FF69B4")},
    {"text": "好友早安，清晨好問候，記得吃份溫暖早餐", "colors": ("#FFFFFF", "#FF4500", "#FFFF00")},
    {"text": "親愛的朋友早安，把煩惱拋開，迎接幸運的一天", "colors": ("#FF69B4", "#FFFFFF", "#FFFFE0")},
    {"text": "祝您早安，平安愉快，天天都有好心情喔", "colors": ("#FFFFE0", "#00FF7F", "#FFFFFF")},
    {"text": "早安你好，讓陽光帶走疲憊，迎接美好新起點", "colors": ("#00BFFF", "#FFFFFF", "#FFFF00")},
    {"text": "大家早安，新的一天，快樂劈里啪啦向你狂奔", "colors": ("#FFFFFF", "#FFD700", "#FF69B4")},
    {"text": "好友早安，元氣滿滿，幸福已經在悄悄敲門囉", "colors": ("#FF4500", "#FFFFFF", "#00FF7F")},
    {"text": "祝您早安，微笑常在，心想事成萬事都順心", "colors": ("#FFFF00", "#FF1493", "#FFFFFF")},
    {"text": "親愛的朋友早安，放鬆心情，享受悠閒的晨光序曲", "colors": ("#FFFFFF", "#00CED1", "#FFA500")},
    {"text": "早安你好，滿滿正能量，今天也是幸運滿分的一天", "colors": ("#FFFF00", "#FF69B4", "#FFFFFF")},
    {"text": "新的一天早安，願舒心的陽光，照亮您前行的每一步", "colors": ("#FFFFFF", "#FF8C00", "#00FF7F")},
    {"text": "早安老友，心中有愛自然溫暖，祝今天事事順心如意", "colors": ("#FF69B4", "#FFFFFF", "#FFFF00")},
    {"text": "大家清晨好，送上一聲真摯問候，願您一整天神采飛揚", "colors": ("#FFFFE0", "#00BFFF", "#FFFFFF")},
    {"text": "溫馨早安，把生活調成喜歡的頻道，今天也要幸福滿滿", "colors": ("#FFFFFF", "#FF1493", "#FFFF00")},
    {"text": "好友早安，生活因知足而美麗，願您的微笑像陽光燦爛", "colors": ("#FFFF00", "#FFFFFF", "#00CED1")},
    {"text": "早安你好，開啟元氣滿滿的一天，好運與您不期而遇", "colors": ("#00FF7F", "#FFFFFF", "#FF4500")},
    {"text": "祝您早安，健康的身體是最大的財富，佳節與平日皆安康", "colors": ("#FFFFFF", "#FFD700", "#FFFFE0")},
    {"text": "清晨早安，生活雖然平凡，但每一天都值得我們熱烈期待", "colors": ("#FF4500", "#FFFFFF", "#FFFF00")},
    {"text": "各位早安，善待自己的心情，讓幸福的感覺裝滿今天", "colors": ("#FFFF00", "#FF69B4", "#FFFFFF")},
    {"text": "好友早安，最美的風景在路上，最真誠的問候在每天清晨", "colors": ("#FFFFFF", "#00BFFF", "#FF8C00")}
]

# 🌅 多達 12 張精心挑選的高畫質、風格完全不同的在地明亮風景、自然與晨光圖庫，確保天天有新鮮感！
BRIGHT_BGS = [
    "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=800&h=600&q=100",  # 綠意原野
    "https://images.unsplash.com/photo-1470240731273-7821a6eeb6bd?auto=format&fit=crop&w=800&h=600&q=100",  # 春天花海
    "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?auto=format&fit=crop&w=800&h=600&q=100",  # 森林晨光
    "https://images.unsplash.com/photo-1472214222541-d510753a8707?auto=format&fit=crop&w=800&h=600&q=100",  # 寧靜鄉間
    "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=800&h=600&q=100",  # 山巒日出
    "https://images.unsplash.com/photo-1418065460487-3e41a6c84dc5?auto=format&fit=crop&w=800&h=600&q=100",  # 陽光樹林
    "https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?auto=format&fit=crop&w=800&h=600&q=100",  # 大自然清新
    "https://images.unsplash.com/photo-1441974231531-c6227db76b6e?auto=format&fit=crop&w=800&h=600&q=100",  # 林間向陽
    "https://images.unsplash.com/photo-1546182990-dffeafbe841d?auto=format&fit=crop&w=800&h=600&q=100",  # 草原晨曦
    "https://images.unsplash.com/photo-1501854140801-50d01698950b?auto=format&fit=crop&w=800&h=600&q=100",  # 遼闊山水
    "https://images.unsplash.com/photo-1595981267035-7b04ca84a82d?auto=format&fit=crop&w=800&h=600&q=100",  # 晨光咖啡桌
    "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=800&h=600&q=100"   # 明亮遠山
]

def check_and_download_font():
    if not os.path.exists(FONT_FILE_NAME):
        try:
            res = requests.get(FONT_URL, timeout=30)
            if res.status_code == 200:
                with open(FONT_FILE_NAME, "wb") as f:
                    f.write(res.content)
        except:
            pass

def get_must_font(size):
    if os.path.exists(FONT_FILE_NAME):
        try: return ImageFont.truetype(FONT_FILE_NAME, size)
        except: pass
    return ImageFont.load_default()

def draw_styled_text(base_img, text, font, main_color, center_y, image_width, is_title=False):
    """👑 保持吳大哥最滿意的圖一狀態：大歪斜度、黑粗框、位置完美居中偏下"""
    try: text_w = ImageDraw.Draw(base_img).textlength(text, font=font)
    except: text_w = len(text) * font.size
    
    text_h = int(font.size * 1.3)
    pad = 60
    txt_img = Image.new("RGBA", (int(text_w + pad * 2), int(text_h + pad * 2)), (0, 0, 0, 0))
    txt_draw = ImageDraw.Draw(txt_img)
    
    x_pos = pad
    y_pos = pad
    
    shadow_offset = 5 if is_title else 3
    txt_draw.text((x_pos + shadow_offset, y_pos + shadow_offset), text, font=font, fill=(0, 0, 0, 220))
    
    border_thickness = 5 if is_title else 3
    for dx in range(-border_thickness, border_thickness + 1):
        for dy in range(-border_thickness, border_thickness + 1):
            if dx*dx + dy*dy <= border_thickness*border_thickness:
                txt_draw.text((x_pos + dx, y_pos + dy), text, font=font, fill="#000000")
                
    txt_draw.text((x_pos, y_pos), text, font=font, fill=main_color)
    
    # 圖一經典靈魂：第一行正的，第二、三行保持 -10.0 度漂亮大歪斜
    skew_angle = 0.0 if is_title else -10.0
    rotated_txt = txt_img.rotate(skew_angle, resample=Image.BICUBIC, expand=True)
    r_w, r_h = rotated_txt.size
    
    base_img.paste(rotated_txt, ((image_width - r_w) // 2, center_y - r_h // 2), rotated_txt)

def get_gemini_quote():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return None
    url = f"https://generatelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    prompt = "請寫一句適合長輩群組、充滿溫馨與正能量的台灣在地早安問候語。字數控制在15到22字之間，中間必須包含一個逗號（，）。嚴禁任何引號、備註、標點符號或解釋，只要這句話本身。"
    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(url, json=payload, timeout=8)
        if res.status_code == 200:
            text = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
            clean_text = text.replace("『", "").replace("』", "").replace('"', '').replace("「", "").replace("」", "").replace("。", "").replace("*", "")
            if "，" in clean_text or "," in clean_text:
                return clean_text
    except:
        pass
    return None

def generate_morning_image(text_content, colors):
    check_and_download_font()
    
    img = None
    # 🎲 每次觸發都真正隨機抽取完全不同的優質風景背景圖
    selected_url = random.choice(BRIGHT_BGS)
    try:
        img_res = requests.get(selected_url, timeout=8)
        if img_res.status_code == 200:
            img = Image.open(BytesIO(img_res.content)).convert("RGB")
    except:
        pass

    if not img:
        img = Image.new("RGB", (800, 600), "#FFBB00")

    img = img.resize((800, 600))
    img = ImageEnhance.Brightness(img).enhance(1.25)
    img = ImageEnhance.Contrast(img).enhance(1.15)
    img = ImageEnhance.Color(img).enhance(1.30)
    
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    for y in range(250, 550):
        alpha = int((y - 250) / 300 * 55)
        ov_draw.line([(0, y), (800, y)], fill=(0, 0, 0, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    
    image_width, _ = img.size

    if "，" in text_content: lines = [line.strip() for line in text_content.split("，") if line.strip()]
    elif "," in text_content: lines = [line.strip() for line in text_content.split(",") if line.strip()]
    else:
        half = len(text_content) // 2
        lines = [text_content[:half], text_content[half:]]
        
    while len(lines) < 3: 
        lines.append("祝您喜樂安康")

    font_line1, font_line2, font_line3 = get_must_font(65), get_must_font(36), get_must_font(34)
    
    # 🎯 圖一黃金高度坐標：第一、二、三行精準定位，絕不重疊
    draw_styled_text(img, lines[0], font_line1, colors[0], 330, image_width, is_title=True)
    draw_styled_text(img, lines[1], font_line2, colors[1], 440, image_width, is_title=False)
    draw_styled_text(img, lines[2], font_line3, colors[2], 530, image_width, is_title=False)
    
    img.save(LOCAL_IMAGE_PATH, "JPEG", quality=98)

def async_task(render_url):
    global IS_PROCESSING
    try:
        LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
        LINE_USER_ID = os.environ.get("LINE_USER_ID")
        if not all([LINE_ACCESS_TOKEN, LINE_USER_ID]): return
            
        ai_text = get_gemini_quote()
        if ai_text:
            text_content = ai_text
            colors = random.choice(STATIC_ROUNDS)["colors"]
        else:
            backup_round = random.choice(STATIC_ROUNDS)
            text_content = backup_round["text"]
            colors = backup_round["colors"]

        # 在背景安全生成新圖片並隨機更換風景
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
        requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload, timeout=15)
    except Exception as e: 
        print(f"背景處理異常: {e}")
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
            return Response("OK", mimetype="text/plain")
        IS_PROCESSING = True
    
    RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
    if not RENDER_EXTERNAL_URL:
        RENDER_EXTERNAL_URL = "https://" + requests.headers.get('Host', '')

    # 🚀 關鍵防禦：收到請求立刻開啟新執行緒去處理，絕不拖延
    threading.Thread(target=async_task, args=(RENDER_EXTERNAL_URL,)).start()
    
    # 🚀 關鍵防禦：0.01秒內立刻回傳極簡文字，徹底根治 cron-job.org 的 Output too large 錯誤！
    return Response("OK", mimetype="text/plain")

@app.route("/")
def home():
    return Response("OK", mimetype="text/plain")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
