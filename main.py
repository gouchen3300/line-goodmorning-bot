import os
import time
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

# 【重大修正】改用專案當前目錄，絕對不會因為 Linux 權限阻擋而導致啟動失敗
FONT_PATH = "NotoSansTC-Bold.ttf"
LOCAL_IMAGE_PATH = "morning_output.jpg"

def download_font_if_not_exists():
    """ 確保伺服器上有繁體中文字體，如果沒有就去下載開源的思源黑體 """
    if not os.path.exists(FONT_PATH):
        print("【系統】正在下載繁體中文字體（思源黑體）...")
        # 更換為極度穩定的字體下載來源
        font_url = "https://github.com/MelonRind/taiwan-fonts/raw/master/ttf/MicrosoftJhengHei-Regular.ttf"
        try:
            res = requests.get(font_url, timeout=30)
            with open(FONT_PATH, "wb") as f:
                f.write(res.content)
            print("【系統】字體下載完成！")
        except Exception as e:
            print(f"【字體下載失敗】: {e}")

def draw_center_text_with_stroke(draw, text, font, image_width, image_height):
    """ 安全的文字置中與自動換行演算法，並加上黑色外框 """
    max_chars_per_line = 10
    lines = [text[i:i+max_chars_per_line] for i in range(0, len(text), max_chars_per_line)]
    
    font_size = font.size
    line_height = int(font_size * 1.3)
    total_text_height = len(lines) * line_height
    
    # 讓整塊文字區域在圖片垂直中央偏下方（早安圖最標準的排版）
    current_y = (image_height - total_text_height) // 2 + 100
    
    for line in lines:
        line_width = len(line) * font_size
        x = (image_width - line_width) // 2
        
        # 繪製黑色文字外框，防止背景太亮看不清
        for offset_x in [-2, 0, 2]:
            for offset_y in [-2, 0, 2]:
                draw.text((x + offset_x, current_y + offset_y), line, font=font, fill="black")
                
        # 繪製正中央的白色主文字
        draw.text((x, current_y), line, font=font, fill="white")
        current_y += line_height

def generate_morning_image():
    download_font_if_not_exists()
    
    # 高畫質晨曦風景底圖
    bg_url = "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=800&auto=format&fit=crop"
    morning_text = "大家早安！祝您今天平安喜樂，順心如意☀️"
    
    try:
        print("【系統】正在下載精美底圖...")
        img_res = requests.get(bg_url, timeout=15, stream=True)
        
        img = Image.open(img_res.raw).convert("RGB")
        img = img.resize((800, 600))
        draw = ImageDraw.Draw(img)
        
        # 載入字體
        if os.path.exists(FONT_PATH):
            font = ImageFont.truetype(FONT_PATH, 42)
        else:
            font = ImageFont.load_default()
            
        # 繪製完美置中字
        draw_center_text_with_stroke(draw, morning_text, font, 800, 600)
        
        # 儲存到當前目錄
        img.save(LOCAL_IMAGE_PATH, "JPEG", quality=90)
        print("【系統】精美早安圖本地生成成功！")
        return True
    except Exception as e:
        print(f"【繪圖失敗】: {e}")
        return False

@app.route("/morning_image.jpg")
def serve_image():
    """ 讓 Render 伺服器直接變成圖床，吐出做好的圖片 """
    if os.path.exists(LOCAL_IMAGE_PATH):
        return send_file(LOCAL_IMAGE_PATH, mimetype="image/jpeg")
    return "Image not found.", 404

@app.route("/trigger")
def trigger():
    LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_USER_ID = os.environ.get("LINE_USER_ID")
    RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
    
    if not all([LINE_ACCESS_TOKEN, LINE_USER_ID]):
        return "【錯誤】環境變數 LINE 未設定！"
        
    if not RENDER_EXTERNAL_URL:
        RENDER_EXTERNAL_URL = "https://" + requests.headers.get('Host', '')

    # 1. 生成圖片
    success = generate_morning_image()
    if not success:
        return "【失敗】圖片生成失敗。"
        
    # 2. 加入防快取時間戳記
    timestamp = int(time.time())
    final_image_url = f"{RENDER_EXTERNAL_URL.rstrip('/')}/morning_image.jpg?t={timestamp}"
    print(f"【LINE 圖片網址】: {final_image_url}")

    # 3. 發送推播
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
        return "【大成功】字體完美置中且帶黑邊的精美早安圖已發送！"
    else:
        return f"【發送失敗】LINE 拒絕，錯誤碼: {line_res.status_code}"

@app.route("/")
def home():
    return "Fix Path Morning Bot is Running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
