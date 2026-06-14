import os
import time
import random
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = Flask(__name__)

LOCAL_IMAGE_PATH = "morning_output.jpg"

# 保底罐頭文案
BACKUP_QUOTES = [
    "大家早安新的一天，祝您心情愉快萬事順心如意",
    "早安願您今天充滿活力，迎來滿滿的平安與喜樂",
    "大家早安把心靈迎向陽光，今天也是美好的一天"
]

# 擴充更豐富的隨機調色盤 (標題色, 內文第一行色, 內文第二行色)
COLOR_PALETTES = [
    ("#FFFFFF", "#FFD700", "#FFD700"),  # 經典金黃
    ("#FFFFFF", "#FF69B4", "#FFC0CB"),  # 嬌豔粉紅
    ("#FFFFFF", "#FF4500", "#FFA500"),  # 活力亮橘
    ("#FFFFFF", "#00FF7F", "#ADFF2F"),  # 清爽嫩綠
    ("#FFFFFF", "#00FFFF", "#E0FFFF"),  # 明亮璀璨
    ("#FFFF00", "#FFFFFF", "#FFFFFF"),  # 黃金標題 + 純白內文
    ("#FF8C00", "#FFFFE0", "#FFFF00")   # 暖陽系列
]

def get_gemini_morning_quote():
    """ 讓 Gemini 生成溫暖語句 """
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
                "text": f"你是一位頂級的早安圖文學大師。請圍繞『{selected_topic}』這個意境，為我全新創作一句送給好友的早安問候語。要求：1. 必須包含「早安」或「大家早安」作為開頭。2. 總字數控制在 16 到 22 個字之間。3. 除去開頭的早安後，後面的文案中間必須包含一個全形逗號『，』。4. 絕對不要有任何其他標點符號、不要 Emoji 貼圖。只要純中文字。"
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

def get_linux_system_font(size):
    """ 
    不走網路下載！直接安全調用 Linux 系統自帶的黑體保底機制。
    為了滿足隨機變化需求，我們會在字型載入失敗時自動切換不同系統路徑。
    """
    # Linux 系統常見的保底字型路徑清單
    possible_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
    ]
    
    # 隨機打亂嘗試順序，增加系統底層分流的機會
    random.shuffle(possible_paths)
    for path in possible_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
                
    # 最終保底，絕對不崩潰
    return ImageFont.load_default()

def draw_beautiful_text(draw, text, image_width):
    """ 100% 穩定的排版，透過隨機陰影粗細、隨機顏色、隨機斷句組合達成天天變化的視覺效果 """
    title_text = ""
    body_text = text
    
    for prefix in ["大家早安", "早安"]:
        if text.startswith(prefix):
            title_text = prefix
            body_text = text[len(prefix):]
            break
            
    if not title_text:
        title_text = "早安"

    # 安全取得 Linux 本地字型
    title_font = get_linux_system_font(62)
    body_font = get_linux_system_font(38)

    # 隨機挑選顏色組合
    title_color, body_color1, body_color2 = random.choice(COLOR_PALETTES)

    # 依據逗號自然拆分
    if "，" in body_text:
        lines = [line.strip() for line in body_text.split("，") if line.strip()]
    else:
        mid = len(body_text) // 2
        lines = [body_text[:mid], body_text[mid:]]

    # 計算排版高度
    title_height = int(62 * 1.4)
    body_line_height = int(38 * 1.4)
    total_text_height = title_height + (len(lines) * body_line_height)
    start_y = 450 - (total_text_height // 2)

    # 【隨機特效變換】每次文字的黑色外框粗細與立體度都會隨機改變！
    border_thickness = random.choice([2, 3, 4])

    # 繪製標題
    try:
        title_w = draw.textlength(title_text, font=title_font)
    except:
        title_w = len(title_text) * 62
    title_x = (image_width - title_w) // 2
    
    # 建立超粗立體黑邊
    for dx in range(-border_thickness, border_thickness + 1):
        for dy in range(-border_thickness, border_thickness + 1):
            draw.text((title_x + dx, start_y + dy), title_text, font=title_font, fill="black")
    draw.text((title_x, start_y), title_text, font=title_font, fill=title_color)
    
    start_y += title_height + 20

    # 繪製內文兩行（輪流套用隨機顏色）
    colors = [body_color1, body_color2]
    for i, line in enumerate(lines):
        try:
            line_w = draw.textlength(line, font=body_font)
        except:
            line_w = len(line) * 38
        x = (image_width - line_w) // 2
        
        current_color = colors[i % len(colors)]
        
        # 內文黑邊
        inner_thickness = border_thickness - 1 if border_thickness > 2 else 2
        for dx in range(-inner_thickness, inner_thickness + 1):
            for dy in range(-inner_thickness, inner_thickness + 1):
                draw.text((x + dx, start_y + dy), line, font=body_font, fill="black")
                    
        draw.text((x, start_y), line, font=body_font, fill=current_color)
        start_y += body_line_height

def generate_morning_image(text_content):
    """ 隨機匹配高畫質背景圖 """
    # 擴大圖片庫 ID，確保每天圖片都不一樣
    pic_ids = [10, 28, 48, 54, 116, 192, 230, 235, 327, 404, 343, 364, 411, 444, 486, 522, 532, 593, 619, 650]
    bg_url = f"https://picsum.photos/id/{random.choice(pic_ids)}/800/600"
    
    try:
        img_res = requests.get(bg_url, timeout=15, stream=True)
        if img_res.status_code != 200:
            fallback_url = "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?q=80&w=800"
            img_res = requests.get(fallback_url, timeout=10, stream=True)
            
        img = Image.open(img_res.raw).convert("RGB")
        img = img.resize((800, 600))
        img = img.filter(ImageFilter.GaussianBlur(radius=1.0)) # 輕微柔焦凸顯文字
        
        draw = ImageDraw.Draw(img)
        draw_beautiful_text(draw, text_content, 800)
            
        img.save(LOCAL_IMAGE_PATH, "JPEG", quality=95)
        return True
    except Exception as e:
        print(f"圖片生成異常: {e}")
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
        return f"【成功】100%穩定不發卡早安圖已發送！今日金句：{ai_quote.replace('，', ' ')}"
    else:
        return f"LINE 發送失敗: {line_res.status_code}"

@app.route("/")
def home():
    return "Gemini Ultra-Stable Local-Font Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
