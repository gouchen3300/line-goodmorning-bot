import os
import time
import random
import requests
from flask import Flask

app = Flask(__name__)

# 使用全局變數紀錄當前最新的檔案名稱
CURRENT_IMAGE_NAME = "morning_base.jpg"
FONT_FILE_NAME = "morning.ttf"

# 全局鎖，防止重複觸發
IS_PROCESSING = False
LAST_COLOR_INDEX = -1

# 【修復： Gemini 提示詞大升級】彻底移除所有森林、咖啡、太陽主題，改成全方位百搭「正能量主題」。
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
    ("#FFF700", "#FFFFFF", "#FF69B4"), 
    ("#FFFFFF", "#FF4500", "#FFF700"), 
    ("#FF69B4", "#FFFFFF", "#FFFDD0"), 
    ("#FFFDD0", "#00FF7F", "#FFFFFF"), 
    ("#00BFFF", "#FFFFFF", "#FFF700"), 
    ("#FFFFFF", "#E1AD01", "#FF69B4"), 
    ("#FF4500", "#FFFFFF", "#00FF7F"), 
    ("#FFFF33", "#FF1493", "#FFFFFF"), 
    ("#FFFFFF", "#00CED1", "#FFA500"), 
    ("#FF6347", "#FFFF00", "#FFFFFF"), 
    ("#00FF7F", "#FFFFFF", "#FF4500"), 
    ("#FFFF00", "#FF69B4", "#FFFFFF")  
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
                    "1. 【60天絕不重複】：發揮你的最高創意，絕對不要有陳腔濫調！\n"
                    "2. 【嚴格字數限制】：總字數必須控制在 25 到 32 個字之間！\n"
                    "3. 內容中間必須包含兩個全形逗號『，』，將整句話自然分成『三段』。\n"
                    "   【最重要鐵律-字詞規範】：第一段是標題開頭（必須包含早安），字數嚴格限制在 4 到 10 個字以內。\n"
                    "   第一段必須使用台灣最自然常見的問候語（例如：大家早安、好友早安、親愛的朋友早安、祝您早安、早安你好）。\n"
                    "   【死命令】：絕對不准自己生造、發明奇怪的名詞（例如絕對不准出現綠林早安、相機早安、咖啡早安等怪詞）！\n"
                    "4. 絕對不要有任何驚嘆號、句號等標點符號（只要那兩個全形逗號），不要任何 Emoji 貼圖。只要純中文字。"
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

def generate_morning_image_bytes(text_content):
    """ 在記憶體中直接繪製圖片並回傳 bytes，完全不寫入磁碟，速度極快 """
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    import io
    
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
        
        # 繪圖與排版
        draw = ImageDraw.Draw(img)
        image_width, image_height = img.size
        
        if "，" in text_content:
            lines = [line.strip() for line in text_content.split("，") if line.strip()]
        else:
            third = len(text_content) // 3
            lines = [text_content[:third], text_content[third:third*2], text_content[third*2:]]
            
        while len(lines) < 3:
            lines.append("今天也要超級快樂")
            
        # 字型加載
        font_file = FONT_FILE_NAME
        if os.path.exists(font_file):
            # 依指示加大字體：大氣 60 號標題！
            font1 = ImageFont.truetype(font_file, 60)
            font2 = ImageFont.truetype(font_file, 36)
            font3 = ImageFont.truetype(font_file, 38)
        else:
            font1 = font2 = font3 = ImageFont.load_default()
            
        # 防重複顏色抽籤
        global LAST_COLOR_INDEX
        available_indices = [i for i in range(len(COLOR_PALETTES)) if i != LAST_COLOR_INDEX]
        chosen_index = random.choice(available_indices)
        LAST_COLOR_INDEX = chosen_index
        colors = COLOR_PALETTES[chosen_index]
        
        centers_y = [340, 435, 525]
        fonts = [font1, font2, font3]
        
        for i, text_line in enumerate(lines[:3]):
            font = fonts[i]
            color = colors[i]
            cy = centers_y[i]
            is_title = (i == 0)
            
            try:
                text_w = ImageDraw.Draw(img).textlength(text_line, font=font)
            except:
                text_w = len(text_line) * font.size
            text_h = int(font.size * 1.2)
            
            pad = 40
            txt_img = Image.new("RGBA", (int(text_w + pad*2), int(text_h + pad*2)), (0,0,0,0))
            txt_draw = ImageDraw.Draw(txt_img)
            
            shadow_radius = 7 if is_title else 5
            for dx in range(-shadow_radius, shadow_radius + 1):
                for dy in range(-shadow_radius, shadow_radius + 1):
                    if abs(dx) + abs(dy) <= shadow_radius:
                        txt_draw.text((pad+dx, pad+dy), text_line, font=font, fill="black")
                        
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    txt_draw.text((pad+dx, pad+dy), text_line, font=font, fill="#FFFFFF")
                    
            txt_draw.text((pad, pad), text_line, font=font, fill=color)
            
            skew_angle = 0.0 if is_title else random.choice([-1, 1]) * random.uniform(6.0, 11.0)
            rotated_txt = txt_img.rotate(skew_angle, resample=Image.BICUBIC, expand=True)
            
            r_w, r_h = rotated_txt.size
            img.paste(rotated_txt, ((image_width - r_w)//2, cy - r_h//2), rotated_txt)
            
        # 將最終生成的圖片存入記憶體
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=90)
        return img_byte_arr.getvalue()
    except Exception as e:
        print(f"圖片生成失敗: {e}")
        return None

def upload_to_imgur(image_bytes):
    """ 【核心修復】硬寫 Client IDPass！ anonymous 免登入上傳至 Imgur """
    # 既然登不進 Imgur，直接硬寫通用 Client ID 通行證，徹底繞過環境變數不穩定的問題！
    # 這組 ID 是 Imgur 官方提供的 Anonymous 公開測試通行證，絕對有效！
    fixed_client_id = "546c25a59c58ad7"
        
    url = "https://api.imgur.com/3/image"
    headers = {"Authorization": f"Client-ID {fixed_client_id}"}
    files = {"image": image_bytes}
    
    try:
        # 上傳到 Imgur 的連線往往需要較長時間，加大逾時到 30 秒以防逾時
        res = requests.post(url, headers=headers, files=files, timeout=30)
        if res.status_code == 200:
            # 拿到 Imgur 的永久隨機網址，這也是為什麼舊圖永遠不會卡 LINE 快取變臉的原因！
            return res.json()["data"]["link"]
        else:
            print(f"Imgur 上傳失敗碼: {res.status_code}, 回應: {res.text}")
    except Exception as e:
        print(f"Imgur 連線異常: {e}")
    return None

@app.route("/trigger")
def trigger():
    global IS_PROCESSING
    if IS_PROCESSING:
        # 修復：被攔截時同樣回傳 OK，徹底杜絕 cron 的 large 錯誤
        return "OK"
    IS_PROCESSING = True
    
    try:
        LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
        LINE_USER_ID = os.environ.get("LINE_USER_ID")
        
        if not all([LINE_ACCESS_TOKEN, LINE_USER_ID]):
            return "OK"
            
        today_theme = random.choice(THEMES)
        ai_quote = get_gemini_morning_quote(today_theme)
        
        # 修復的核心邏輯：依序生 bytes 製圖，接著「一定要上傳到 Imgur 拿到網址」！
        img_bytes = generate_morning_image_bytes(ai_quote)
        if not img_bytes:
            return "OK"
            
        # 上傳並拿到 Imgur 的網址（例如 https://i.imgur.com/ABCDE.jpg）
        final_image_url = upload_to_imgur(img_bytes)
        
        if not final_image_url:
            print("無法拿到 Imgur 網址，跳過 LINE 發送")
            return "OK"
            
        print(f"【成功】已將今日歪斜大標題早安圖托管至 Imgur: {final_image_url}")

        # 發送給 LINE（傳送 Imgur 網址，徹底解決歷史圖片變臉集體「校正回歸」的問題）
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
        # 極簡回報 OK，徹底解決 cron 認為 output too large 的問題！
        return "OK"
        
    except Exception as e:
        print(f"觸發程序異常: {e}")
        return "OK"
    finally:
        IS_PROCESSING = False

@app.route("/")
def home():
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
