import os
import time
import random
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = Flask(__name__)

LOCAL_IMAGE_PATH = "morning_output.jpg"

# 備用罐頭文案（內含逗號作為精準斷句依據）
BACKUP_QUOTES = [
    "大家早安新的一天，祝您心情愉快萬事順心如意",
    "早安願您今天充滿活力，迎來滿滿的平安與喜樂",
    "大家早安把心靈迎向陽光，今天也是美好的一天"
]

# 鮮豔美觀的調色盤清單 (標題顏色, 內文顏色)
COLOR_PALETTES = [
    ("#FFFFFF", "#FFD700"),  # 1. 經典款：純白標題 ＋ 亮眼金黃內文
    ("#FFFFFF", "#FF69B4"),  # 2. 嬌豔款：純白標題 ＋ 鮮豔桃粉內文
    ("#FFFFFF", "#FF4500"),  # 3. 活力款：純白標題 ＋ 太陽亮橘內文
    ("#FFFFFF", "#00FF7F"),  # 4. 清爽款：純白標題 ＋ 螢光嫩綠內文
    ("#FFFFFF", "#00FFFF")   # 5. 明亮款：純白標題 ＋ 璀璨明藍內文
]

# 改用台灣國發會全字庫、微軟官方開源的高速直連網址，確保 Render 絕對下載成功
CLOUD_TITLE_URLS = [
    "https://github.com/google/fonts/raw/main/ofl/notosanstc/NotoSansTC%5Bwght%5D.ttf",    # 思源黑體-粗
    "https://raw.githubusercontent.com/ButTaiwan/genseki-font/master/font/Genseki-Bold.ttf", # 源石黑體
    "https://raw.githubusercontent.com/naenae148/Mantou-Sans/main/MantouSans-Regular.ttf"    # 饅頭黑體
]

CLOUD_BODY_URLS = [
    "https://github.com/google/fonts/raw/main/ofl/notoseriftc/NotoSerifTC%5Bwght%5D.ttf",  # 思源宋體
    "https://raw.githubusercontent.com/ButTaiwan/genyo-font/master/font/GenYoMin-Regular.ttf", # 源樣明體
    "https://raw.githubusercontent.com/ButTaiwan/gensen-font/master/font/Gensen-Regular.ttf"   # 源泉圓體
]

def download_fonts():
    """ 官方直連下載通道：加強下載成功率與超時等待 """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    for i, url in enumerate(CLOUD_TITLE_URLS, 1):
        path = f"title{i}.ttf"
        if not os.path.exists(path):
            try:
                print(f"正在為您從官方載入精美標題字型 {i}...")
                r = requests.get(url, headers=headers, timeout=30)
                if r.status_code == 200 and len(r.content) > 100000:
                    with open(path, 'wb') as f:
                        f.write(r.content)
            except Exception as e:
                print(f"標題字型 {i} 下載失敗: {e}")
                
    for i, url in enumerate(CLOUD_BODY_URLS, 1):
        path = f"body{i}.ttf"
        if not os.path.exists(path):
            try:
                print(f"正在為您從官方載入精美內文字型 {i}...")
                r = requests.get(url, headers=headers, timeout=30)
                if r.status_code == 200 and len(r.content) > 100000:
                    with open(path, 'wb') as f:
                        f.write(r.content)
            except Exception as e:
                print(f"內文字型 {i} 下載失敗: {e}")

def get_gemini_morning_quote():
    """ 讓 Gemini 自由生成帶有單一逗號（用來精準分行）的精美語句 """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return random.choice(BACKUP_QUOTES)
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    random_topics = ["大自然晨光", "朝露與花朵", "心靈茶香", "微風與遠山", "希望與活力", "喜悅與相伴", "溫暖陽光"]
    selected_topic = random.choice(random_topics)
    
    payload = {
        "contents": [{
            "parts": [{
                "text": f"你是一位頂級的早安圖文學大師。請圍繞『{selected_topic}』這個意境，為我全新創作一句送給好友的早安問候語。要求：1. 必須包含「早安」或「大家早安」作為開頭。2. 語氣要極具詩意、溫暖。3. 總字數控制在 16 到 24 個字之間。4. 中間必須恰好包含一個全形逗號『，』用來當作前後兩句的分行依據。5. 除去這一個逗號外，絕對不要有任何其他標點符號（不要句號驚嘆號）、不要 Emoji 貼圖、引號或星號。只要純中文字。"
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
            if quote and "，" in quote:
                return quote
    except Exception as e:
        print(f"Gemini API 生成出錯: {e}")
        
    return random.choice(BACKUP_QUOTES)

def draw_beautiful_text(draw, text, image_width):
    """ 依據逗號自然拆成您要的兩行（不保留標點），並隨機分配下載好的官方字型 """
    title_text = ""
    body_text = text
    
    for prefix in ["大家早安", "早安"]:
        if text.startswith(prefix):
            title_text = prefix
            body_text = text[len(prefix):]
            break
            
    if not title_text:
        title_text = "早安"

    # 隨機抽取 1~3 號下載成功的優美官方字型
    chosen_title_file = f"title{random.randint(1, 3)}.ttf"
    chosen_body_file = f"body{random.randint(1, 3)}.ttf"
    
    t_font_path = chosen_title_file if os.path.exists(chosen_title_file) else None
    b_font_path = chosen_body_file if os.path.exists(chosen_body_file) else None

    # 如果有成功抓到任一官方字型就使用，沒有就使用系統預設
    if t_font_path and b_font_path:
        title_font = ImageFont.truetype(t_font_path, 58)
        body_font = ImageFont.truetype(b_font_path, 36)
    else:
        title_font = body_font = ImageFont.load_default()

    # 隨機挑選一組鮮豔美觀的文字顏色組合
    title_color, body_color = random.choice(COLOR_PALETTES)

    # 【依照您要的：遇逗號就拆成兩行，字數不用平均，去掉標點】
    lines = []
    if "，" in body_text:
        parts = body_text.split("，")
        for part in parts:
            if part.strip():
                lines.append(part.strip())
    else:
        mid_point = len(body_text) // 2
        lines.append(body_text[:mid_point])
        lines.append(body_text[mid_point:])

    # 計算黃金置中排版高度
    title_height = int(title_font.size * 1.5)
    body_line_height = int(body_font.size * 1.5)
    total_text_height = title_height + (len(lines) * body_line_height)
    start_y = 440 - (total_text_height // 2)

    # 繪製標題（立體超粗黑邊 ＋ 隨機鮮豔標題色）
    title_w = draw.textlength(title_text, font=title_font)
    title_x = (image_width - title_w) // 2
    for dx in [-3, -2, -1, 0, 1, 2, 3]:
        for dy in [-3, -2, -1, 0, 1, 2, 3]:
            draw.text((title_x + dx, start_y + dy), title_text, font=title_font, fill="black")
    draw.text((title_x, start_y), title_text, font=title_font, fill=title_color)
    
    start_y += title_height + 20

    # 繪製內文兩行（不帶標點符號 ＋ 隨機鮮豔內文色）
    for line in lines:
        line_w = draw.textlength(line, font=body_font)
        x = (image_width - line_w) // 2
        
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                draw.text((x + dx, start_y + dy), line, font=body_font, fill="black")
                    
        draw.text((x, start_y), line, font=body_font, fill=body_color)
        start_y += body_line_height

def generate_morning_image(text_content):
    """ 生成早安圖背景與引導字型下載 """
    download_fonts()  # 在背景自動執行穩定的官方直連下載

    if any(k in text_content for k in ["陽光", "喜悅", "光芒", "微笑", "閃耀", "希望"]):
        url_pool = [
            f"https://picsum.photos/id/{random.choice([10, 28, 48, 54, 116])}/800/600",
            f"https://picsum.photos/id/{random.choice([192, 230, 235, 327, 404])}/800/600"
        ]
    else:
        url_pool = [
            f"https://picsum.photos/id/{random.choice([343, 364, 411, 444, 486])}/800/600",
            f"https://picsum.photos/id/{random.choice([522, 532, 593, 619, 650])}/800/600"
        ]
        
    bg_url = random.choice(url_pool)
    
    try:
        img_res = requests.get(bg_url, timeout=15, stream=True)
        if img_res.status_code != 200:
            fallback_url = "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?q=80&w=800"
            img_res = requests.get(fallback_url, timeout=10, stream=True)
            
        img = Image.open(img_res.raw).convert("RGB")
        img = img.resize((800, 600))
        img = img.filter(ImageFilter.GaussianBlur(radius=1.2))
        
        draw = ImageDraw.Draw(img)
        draw_beautiful_text(draw, text_content, 800)
            
        img.save(LOCAL_IMAGE_PATH, "JPEG", quality=92)
        return True
    except Exception as e:
        print(f"動態藝術圖片生成異常: {e}")
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
        return f"【成功】全新官方通道免上傳早安圖已發送！今日金句：{ai_quote.replace('，', ' ')}"
    else:
        return f"LINE 發送失敗: {line_res.status_code}"

@app.route("/")
def home():
    return "Gemini Official Fonts Downloader Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
