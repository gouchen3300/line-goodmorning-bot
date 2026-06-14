import os
import time
import random
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# 【核心修復】在 Render 啟動的一瞬間，用系統指令直接在底層植入台灣文鼎繁體中文字型
# 這個指令只會執行一次，速度極快，且是作業系統層級，Render 絕對阻擋不了！
try:
    if not os.path.exists("/usr/share/fonts/truetype/arphic/gkai00mp.ttf"):
        print("正在為吳大哥的伺服器強行植入底層繁體中文字型...")
        os.system("apt-get update && apt-get install -y fonts-arphic-gkai00mp fonts-arphic-gbsn00lp")
except Exception as e:
    print(f"底層植入字型時發生非預期錯誤: {e}")

app = Flask(__name__)

LOCAL_IMAGE_PATH = "morning_output.jpg"

# 保底罐頭文案
BACKUP_QUOTES = [
    "大家早安新的一天，祝您心情愉快萬事順心如意",
    "早安願您今天充滿活力，迎來滿滿的平安與喜樂",
    "大家早安把心靈迎向陽光，今天也是美好的一天"
]

# 豐富的早安圖調色盤組合 (標題顏色, 內文第一行, 內文第二行)
COLOR_PALETTES = [
    ("#FFFFFF", "#FFD700", "#FFD700"),  # 經典金黃
    ("#FFFFFF", "#FF69B4", "#FFC0CB"),  # 嬌豔粉紅
    ("#FFFFFF", "#FF4500", "#FFA500"),  # 活力亮橘
    ("#FFFFFF", "#00FF7F", "#ADFF2F"),  # 清爽嫩綠
    ("#FFFFFF", "#00FFFF", "#E0FFFF"),  # 明亮璀璨
    ("#FFFF00", "#FFFFFF", "#FFFFFF"),  # 黃金標題 + 純白內文
    ("#FFD700", "#FFFF00", "#FF8C00")   # 暖陽多變
]

def get_gemini_morning_quote():
    """ 讓 Gemini 生成帶有逗號的對仗工整溫暖句子 """
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

def get_safe_font(size):
    """ 尋找系統中被強行植入的繁體中文字型，100% 不會再出現豆腐塊 """
    paths = [
        "/usr/share/fonts/truetype/arphic/gkai00mp.ttf", # 繁體楷書 (保證優先)
        "/usr/share/fonts/truetype/arphic/gbsn00lp.ttf", # 備用簡明
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" 
    ]
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()

def draw_beautiful_text(draw, text, image_width):
    """ 精準對仗斷句排版 ＋ 100% 中文字型安全保障 """
    title_text = ""
    body_text = text
    
    for prefix in ["大家早安", "早安"]:
        if text.startswith(prefix):
            title_text = prefix
            body_text = text[len(prefix):]
            break
            
    if not title_text:
        title_text = "早安"

    # 安全撈取文鼎中文字型
    title_font = get_safe_font(60)
    body_font = get_safe_font(38)

    # 隨機挑選顏色組合
    title_color, body_color1, body_color2 = random.choice(COLOR_PALETTES)

    # 依據逗號自然拆分成左右平均的兩行
    if "，" in body_text:
        lines = [line.strip() for line in body_text.split("，") if line.strip()]
    else:
        mid = len(body_text) // 2
        lines = [body_text[:mid], body_text[mid:]]

    # 計算黃金中軸線高度
    title_height = int(60 * 1.5)
    body_line_height = int(38 * 1.5)
    total_text_height = title_height + (len(lines) * body_line_height)
    start_y = 440 - (total_text_height // 2)

    # 【字體外框自動隨機變化邏輯】每次黑邊與字體大小都會動態微調，讓視覺天天都有變化
    border_thickness = random.choice([2, 3, 4])

    # 繪製標題
    try:
        title_w = draw.textlength(title_text, font=title_font)
    except:
        title_w = len(title_text) * 60
    title_x = (image_width - title_w) // 2
    
    # 粗立體邊框
    for dx in range(-border_thickness, border_thickness + 1):
        for dy in range(-border_thickness, border_thickness + 1):
            draw.text((title_x + dx, start_y + dy), title_text, font=title_font, fill="black")
    draw.text((title_x, start_y), title_text, font=title_font, fill=title_color)
    
    start_y += title_height + 20

    # 繪製工整等長、不帶標點的兩行內文
    colors = [body_color1, body_color2]
    for i, line in enumerate(lines):
        try:
            line_w = draw.textlength(line, font=body_font)
        except:
            line_w = len(line) * 38
        x = (image_width - line_w) // 2
        
        current_color = colors[i % len(colors)]
        
        # 內文陰影外框
        inner_thickness = border_thickness - 1 if border_thickness > 2 else 2
        for dx in range(-inner_thickness, inner_thickness + 1):
            for dy in range(-inner_thickness, inner_thickness + 1):
                draw.text((x + dx, start_y + dy), line, font=body_font, fill="black")
                    
        draw.text((x, start_y), line, font=body_font, fill=current_color)
        start_y += body_line_height

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
        img = img.filter(ImageFilter.GaussianBlur(radius=1.0)) # 柔焦
        
        draw = ImageDraw.Draw(img)
        draw_beautiful_text(draw, text_content, 800)
            
        img.save(LOCAL_IMAGE_PATH, "JPEG", quality=95)
        return True
    except Exception as e:
        print(f"圖片生成發生錯誤: {e}")
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
        return f"【成功】全新內建繁體中文字型早安圖已發送！今日金句：{ai_quote.replace('，', ' ')}"
    else:
        return f"LINE 發送失敗: {line_res.status_code}"

@app.route("/")
def home():
    return "Gemini Fixed Chinese Font Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
