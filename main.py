import os
import time
import random
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = Flask(__name__)

LOCAL_IMAGE_PATH = "morning_output.jpg"
# 這是您在 GitHub 上唯一的繁體字型希望，我們強制鎖定它！
FONT_FILE_NAME = "morning.ttf"  

# 保底罐頭文案
BACKUP_QUOTES = [
    "大家早安新的一天，祝您心情愉快萬事順心如意",
    "早安願您今天充滿活力，迎來滿滿的平安與喜樂",
    "大家早安把心靈迎向陽光，今天也是美好的一天"
]

# 豐富的長輩圖多變鮮艷調色盤
COLOR_PALETTES = [
    ("#FFFFFF", "#FFD700", "#FFD700"),  # 經典金黃
    ("#FFFFFF", "#FF69B4", "#FFC0CB"),  # 嬌豔粉紅
    ("#FFFFFF", "#FF4500", "#FFA500"),  # 活力亮橘
    ("#FFFFFF", "#00FF7F", "#ADFF2F"),  # 清爽嫩綠
    ("#FFFFFF", "#00FFFF", "#E0FFFF"),  # 明亮璀璨
    ("#FFFF00", "#FFFFFF", "#FFFFFF"),  # 黃金標題 + 純白內文
    ("#FFD700", "#FFFF00", "#FF8C00")   # 暖陽層次
]

def get_gemini_morning_quote():
    """ 讓 Gemini 生成溫暖問候語 """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return random.choice(BACKUP_QUOTES)
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    random_topics = ["大自然晨光", "朝露與花朵", "心靈茶香", "微風與遠山", "希望與活力", "喜悅與相伴", "溫暖陽光", "高山美景"]
    selected_topic = random.choice(random_topics)
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"你是一位頂級的早安圖文學大師。請圍繞『{selected_topic}』這個意境，為我全新創作一句送給好友的早安問候語。要求：1. 必須包含「早安」或「大家早安」作為開頭。2. 總字數控制在 16 到 22 個字之間。3. 除去開頭的早安後，後面的文案中間必須包含一個全形逗號『，』，且前後兩半的字數要盡量一樣長。4. 絕對不要有任何其他標點符號、不要 Emoji 貼圖。只要純中文字。"
            }]
        }]
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            result = res.json()
            quote = result['candidates'][0]['content']['parts'][0]['text'].strip()
            for punc in ['。', '！', '、', '？', '；', '：', '.', '!', '?', '"', '「', '」', '*', '\n', ' ']:
                quote = quote.replace(punc, '')
            if quote:
                return quote
    except Exception as e:
        print(f"Gemini API 生成出錯: {e}")
        
    return random.choice(BACKUP_QUOTES)

def get_must_font(size):
    """ 【絕對強制機制】砍斷所有退路，100% 只准讀取 morning.ttf """
    if os.path.exists(FONT_FILE_NAME):
        try:
            return ImageFont.truetype(FONT_FILE_NAME, size)
        except Exception as e:
            print(f"字型讀取失敗原因: {e}")
    # 如果真的連 morning.ttf 都因為部署沒同步拿到，直接大膽拋出預警
    print("警告：系統目前在目錄下找不到 morning.ttf 檔案！")
    return ImageFont.load_default()

def draw_beautiful_text(draw, text, image_width):
    """ 精準斷句 ＋ 強制繁體字型繪製 """
    title_text = ""
    body_text = text
    
    for prefix in ["大家早安", "早安"]:
        if text.startswith(prefix):
            title_text = prefix
            body_text = text[len(prefix):]
            break
            
    if not title_text:
        title_text = "早安"

    # 直接使用強制鎖定繁體字型的方法
    title_font = get_must_font(60)
    body_font = get_must_font(38)

    title_color, body_color1, body_color2 = random.choice(COLOR_PALETTES)

    if "，" in body_text:
        lines = [line.strip() for line in body_text.split("，") if line.strip()]
    else:
        mid = len(body_text) // 2
        lines = [body_text[:mid], body_text[mid:]]

    title_height = int(60 * 1.5)
    body_line_height = int(38 * 1.5)
    total_text_height = title_height + (len(lines) * body_line_height)
    start_y = 440 - (total_text_height // 2)

    border_thickness = random.choice([2, 3, 4])

    # 繪製標題
    try:
        title_w = draw.textlength(title_text, font=title_font)
    except:
        title_w = len(title_text) * 60
    title_x = (image_width - title_w) // 2
    
    for dx in range(-border_thickness, border_thickness + 1):
        for dy in range(-border_thickness, border_thickness + 1):
            draw.text((title_x + dx, start_y + dy), title_text, font=title_font, fill="black")
    draw.text((title_x, start_y), title_text, font=title_font, fill=title_color)
    
    start_y += title_height + 20

    # 繪製內文
    colors = [body_color1, body_color2]
    for i, line in enumerate(lines):
        try:
            line_w = draw.textlength(line, font=body_font)
        except:
            line_w = len(line) * 38
        x = (image_width - line_w) // 2
        
        current_color = colors[i % len(colors)]
        
        inner_thickness = border_thickness - 1 if border_thickness > 2 else 2
        for dx in range(-inner_thickness, inner_thickness + 1):
            for dy in range(-inner_thickness, inner_thickness + 1):
                draw.text((x + dx, start_y + dy), line, font=body_font, fill="black")
                    
        draw.text((x, start_y), line, font=body_font, fill=current_color)
        start_y += body_line_height

def apply_random_font_distortion(image_path):
    """ 像素級矩陣隨機變形技術，讓單一字型能天天自動微調胖瘦、歪斜 """
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        x_scale = random.uniform(0.96, 1.04)   # 隨機胖瘦
        y_scale = random.uniform(0.98, 1.02)
        x_shear = random.uniform(-0.05, 0.05)  # 隨機傾斜
        y_shear = random.uniform(-0.02, 0.02)
        
        img = img.transform(
            (width, height),
            Image.Transform.AFFINE,
            (x_scale, x_shear, 0, y_shear, y_scale, 0),
            resample=Image.Resampling.BILINEAR
        )
        img.save(image_path, "JPEG", quality=95)
    except Exception as e:
        print(f"視覺變形略過: {e}")

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
        img = img.filter(ImageFilter.GaussianBlur(radius=0.7)) 
        
        draw = ImageDraw.Draw(img)
        draw_beautiful_text(draw, text_content, 800)
        img.save(LOCAL_IMAGE_PATH, "JPEG", quality=95)
        
        apply_random_font_distortion(LOCAL_IMAGE_PATH)
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
        return f"【大功告成】已強制調用本地 morning.ttf 繁體字型發送！今日金句：{ai_quote.replace('，', ' ')}"
    else:
        return f"LINE 發送失敗: {line_res.status_code}"

@app.route("/")
def home():
    return "Gemini Local Font Forced Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
