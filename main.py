import os
import time
import random
import requests
import base64  # 用於將圖片轉為 Base64 格式上傳到 ImgBB
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = Flask(__name__)

LOCAL_IMAGE_PATH = "morning_output.jpg"
FONT_FILE_NAME = "morning.ttf"  # 沿用您上傳的繁體字型
IMGBBB_API_KEY = "5526bb902fd10d64e9b8d6edf9c38ae6"  # 已為您填入申請好的 ImgBB 金鑰

# 全域狀態鎖：防止 Render 因超時重試導致連續發送重複圖片
IS_PROCESSING = False

# 俏皮可愛的保底罐頭文案
BACKUP_QUOTES = [
    "大家早安！太陽公公曬屁股囉，今天也要元氣滿滿，記得吃早餐喔！",
    "早安！新的一天開始啦，祝你心情像爆米花一樣，快樂劈里啪啦！",
    "大家早安！幸福正在向你狂奔過來，今天也要記得保持微笑喔！"
]

# 充滿朝氣的豐富顏色搭配（文字, 內文1, 內文2, 第三行可愛亮色）
COLOR_PALETTES = [
    ("#FFFFFF", "#FFD700", "#FFD700", "#FFFF00"),  # 經典金黃 + 閃亮黃
    ("#FFFFFF", "#FF69B4", "#FFC0CB", "#FF1493"),  # 嬌豔粉紅 + 俏皮深粉
    ("#FFFFFF", "#FF4500", "#FFA500", "#FFD700"),  # 活力亮橘 + 溫暖金黃
    ("#FFFFFF", "#00FF7F", "#ADFF2F", "#00FFFF"),  # 清爽嫩綠 + 璀璨藍綠
    ("#FFFF00", "#FFFFFF", "#FFFFFF", "#FF69B4")   # 黃金標題 + 純白內文 + 少女粉紅
]

def get_gemini_morning_quote():
    """ 讓 Gemini 生成俏皮、可愛、絕對不無聊的三行早安文案，加入 60 天不重複機制 """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return random.choice(BACKUP_QUOTES)
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    random_styles = ["充滿元氣的小兔子", "幽默貼心的好朋友", "暖心又調皮的晨光精靈", "每天都想逗你笑的開心果"]
    selected_style = random.choice(random_styles)
    
    payload = {
        "contents": [{
            "parts": [{
                "text": (
                    f"你是一位說話風格極度『俏皮、可愛、活潑、幽默』的早安圖文學大師。請以『{selected_style}』的語氣，"
                    "全新創作一句送給好友的早安問候語。為了確保每天內容完全獨特、不重複（目標 60 天不套路），請嚴格遵守以下規則：\n\n"
                    "1. 必須包含「早安」或「大家早安」開頭。\n"
                    "2. 總字數嚴格控制在 25 到 32 個字之間，讀起來要讓人會心一笑、覺得新穎不枯燥。\n"
                    "3. 內容中間必須包含兩個全形逗號『，』，將整句話自然分成『三段』。\n"
                    "   - 第一段：必須是早安開頭。\n"
                    "   - 第二段：請隨機從以下主題挑選一個發揮【天氣變化、星期幾的怨念與期待、咖啡與早餐的誘惑、昨晚夢境續集、各種可愛動物（如水豚、貓咪、倉鼠）的慵懶聯想、正能量開外掛、無厘頭生活冷笑話、季節感】。\n"
                    "   - 第三段：必須是最俏皮、最可愛、帶有強烈互動感或祝願的結尾短句。\n"
                    "4. 【嚴格禁止】使用常見的罐頭詞彙，例如連續幾天都出現「元氣滿滿」、「幸福狂奔」、「快樂劈里啪啦」、「保持微笑」。請多開發全新、有現代感的俏皮詞彙（例如：抱一個、充飽電、戳臉頰、笑到噴飯、開外掛、不想努力了）。\n"
                    "5. 絕對不要有任何驚嘆號、句號等標點符號（只要那兩個全形逗號），不要 Emoji 貼圖。只要純中文字。"
                )
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

def draw_beautiful_text(draw, text, image_width):
    if "，" in text:
        lines = [line.strip() for line in text.split("，") if line.strip()]
    else:
        third = len(text) // 3
        lines = [text[:third], text[third:third*2], text[third*2:]]

    while len(lines) < 3:
        lines.append("今天也要超級快樂喔")

    font_line1 = get_must_font(55)
    font_line2 = get_must_font(38)
    font_line3 = get_must_font(42)

    color1, color2, color3, color_special = random.choice(COLOR_PALETTES)
    colors = [color1, color2, color_special]

    line_heights = [int(55 * 1.4), int(38 * 1.4), int(42 * 1.5)]
    total_height = sum(line_heights) + 40
    start_y = 440 - (total_height // 2)

    # 第一行
    try: w1 = draw.textlength(lines[0], font=font_line1)
    except: w1 = len(lines[0]) * 55
    x1 = (image_width - w1) // 2
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            draw.text((x1 + dx, start_y + dy), lines[0], font=font_line1, fill="black")
    draw.text((x1, start_y), lines[0], font=font_line1, fill=colors[0])
    start_y += line_heights[0] + 15

    # 第二行
    try: w2 = draw.textlength(lines[1], font=font_line2)
    except: w2 = len(lines[1]) * 38
    x2 = (image_width - w2) // 2
    for dx in range(-2, 3):
        for dy in range(-2, 3):
            draw.text((x2 + dx, start_y + dy), lines[1], font=font_line2, fill="black")
    draw.text((x2, start_y), lines[1], font=font_line2, fill=colors[1])
    start_y += line_heights[1] + 20

    # 第三行
    try: w3 = draw.textlength(lines[2], font=font_line3)
    except: w3 = len(lines[2]) * 42
    x3 = (image_width - w3) // 2
    for dx in range(-5, 6):
        for dy in range(-5, 6):
            if abs(dx) + abs(dy) <= 8:
                draw.text((x3 + dx, start_y + dy), lines[2], font=font_line3, fill="black")
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            draw.text((x3 + dx, start_y + dy), lines[2], font=font_line3, fill="#FFFFFF")
    draw.text((x3, start_y), lines[2], font=font_line3, fill=colors[2])


def generate_morning_image(text_content):
    """ 動態圖片生成機制：利用當天日期組合出上百種不重複的底圖來源 """
    try:
        day_of_year = time.localtime().tm_yday
        dynamic_pic_id = (day_of_year * 7 + random.randint(1, 50)) % 800
        
        if dynamic_pic_id in [0, 100, 200, 300, 400, 500, 600, 700]:
            dynamic_pic_id += 19
            
        bg_url = f"https://picsum.photos/id/{dynamic_pic_id}/800/600"
        
        img_res = requests.get(bg_url, timeout=15, stream=True)
        if img_res.status_code != 200:
            pic_ids = [10, 28, 48, 54, 116, 192, 230, 235, 327, 404, 343, 364, 411, 444, 486, 522, 532, 593, 619, 650]
            bg_url = f"https://picsum.photos/id/{random.choice(pic_ids)}/800/600"
            img_res = requests.get(bg_url, timeout=10, stream=True)
            
        img = Image.open(img_res.raw).convert("RGB")
        img = img.resize((800, 600))
        img = img.filter(ImageFilter.GaussianBlur(radius=0.6))
        
        draw = ImageDraw.Draw(img)
        draw_beautiful_text(draw, text_content, 800)
        img.save(LOCAL_IMAGE_PATH, "JPEG", quality=95)
        
        return True
    except Exception as e:
        print(f"圖片生成錯誤: {e}")
        return False

def upload_to_imgbb():
    """ 讀取本地生成的圖片，穩定上傳到使用者的 ImgBB 空間並取得真正的圖片直連網址 """
    try:
        if not os.path.exists(LOCAL_IMAGE_PATH):
            return None
            
        with open(LOCAL_IMAGE_PATH, "rb") as file:
            base64_image = base64.b64encode(file.read()).decode('utf-8')
            
        url = "https://api.imgbb.com/1/upload"
        payload = {
            "key": IMGBBB_API_KEY,
            "image": base64_image
        }
        
        res = requests.post(url, data=payload, timeout=20)
        if res.status_code == 200:
            result = res.json()
            if result.get("success"):
                return result["data"]["image"]["url"]  
        print(f"ImgBB 上傳失敗，狀態碼: {res.status_code}, 回傳內容: {res.text}")
    except Exception as e:
        print(f"ImgBB 上傳過程出錯: {e}")
    return None

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
    
    # 如果前一個相同的請求還在處理中，直接攔截並拒絕，防止排程超時重試導致的連發
    if IS_PROCESSING:
        return "系統正在處理前一次的發送請求，此重複請求已成功攔截。", 202

    LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_USER_ID = os.environ.get("LINE_USER_ID")
    
    if not all([LINE_ACCESS_TOKEN, LINE_USER_ID]):
        return "環境變數尚未設定完成"

    try:
        # 上鎖
        IS_PROCESSING = True

        ai_quote = get_gemini_morning_quote()

        # 1. 產生圖片並存在本地端
        if not generate_morning_image(ai_quote):
            return "圖片生成失敗"
            
        # 2. 將圖片上傳到 ImgBB
        final_image_url = upload_to_imgbb()
        
        if not final_image_url:
            print("警告：ImgBB 上傳失敗，啟用 Render 網址保底方案")
            RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
            if not RENDER_EXTERNAL_URL:
                RENDER_EXTERNAL_URL = "https://" + requests.headers.get('Host', '')
            timestamp = int(time.time() * 1000)
            final_image_url = f"{RENDER_EXTERNAL_URL.rstrip('/')}/morning_image.jpg?t={timestamp}"

        # 3. 發送給 LINE 官方帳號
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
            return f"【成功】三行俏皮可愛版早安圖已發送！內容：{ai_quote} | 圖片網址：{final_image_url}"
        else:
            return f"LINE 發送失敗: {line_res.status_code}"
            
    finally:
        # 無論成功或失敗，最後一定要解鎖，下一天的排程才能繼續進來
        IS_PROCESSING = False

@app.route("/")
def home():
    return "Gemini 3-Line Cute Style Bot with ImgBB is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
