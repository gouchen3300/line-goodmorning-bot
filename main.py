import os
import time
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

# 將產出的圖片直接存在當前專案資料夾內，最安全不卡權限
LOCAL_IMAGE_PATH = "morning_output.jpg"

def draw_safe_wrapped_text(draw, text, font, image_width, image_height):
    """ 
    使用 Python 內建最安全的文字長度計算，
    自動偵測邊界換行，並將文字完美鎖定在圖片中央偏下方的安全區域。
    """
    lines = []
    current_line = ""
    
    # 逐字檢查，如果超過圖片寬度 (留 80 像素邊距) 就自動換行
    for char in text:
        test_line = current_line + char
        # 使用內建的 textlength 精準計算當前字串的像素寬度
        if draw.textlength(test_line, font=font) < (image_width - 80):
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = char
    if current_line:
        lines.append(current_line)
        
    # 萬一字數真的太長被切成多行，計算出正確的總高度以進行垂直置中
    line_height = 55
    total_text_height = len(lines) * line_height
    
    # 將文字區塊固定放在畫面中央偏下（y=380），這是早安圖最舒適的視覺位置
    start_y = 380 - (total_text_height // 2)
    
    for line in lines:
        # 精準計算出這行字要置中所需要的 X 座標
        line_width = draw.textlength(line, font=font)
        x = (image_width - line_width) // 2
        
        # 【精美度大升級】繪製 360 度立體陰影外框（上下左右、斜角全面覆蓋）
        # 這樣做可以確保不論底圖多亮、陽光多刺眼，白色的字體都絕對清晰好看
        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if dx != 0 or dy != 0:
                    draw.text((x + dx, start_y + dy), line, font=font, fill="black")
                    
        # 繪製最上層的純白亮色主文字
        draw.text((x, start_y), line, font=font, fill="white")
        start_y += line_height

def generate_morning_image():
    # 使用高畫質且連線極度穩定的 Unsplash 官方風景圖作為底圖
    bg_url = "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=800&auto=format&fit=crop"
    morning_text = "大家早安！祝您今天平安喜樂，順心如意☀️"
    
    try:
        print("【系統】正在下載穩定的背景底圖...")
        img_res = requests.get(bg_url, timeout=10, stream=True)
        if img_res.status_code != 200:
            return False
            
        img = Image.open(img_res.raw).convert("RGB")
        img = img.resize((800, 600)) # 強制將底圖調整為標準高畫質黃金比例
        draw = ImageDraw.Draw(img)
        
        # 載入萬用預設字體，並放大到 45 級字（大字長輩最愛）
        # 這樣做 100% 免去下載檔案的風險，Render 絕對放行
        try:
            font = ImageFont.load_default(size=45)
        except TypeError:
            # 預防舊版本 Pillow 不支援 size 參數的萬備防禦機制
            font = ImageFont.load_default()
            
        print("【系統】正在進行文字排版與立體黑邊壓製...")
        draw_safe_wrapped_text(draw, morning_text, font, 800, 600)
        
        # 儲存成品
        img.save(LOCAL_IMAGE_PATH, "JPEG", quality=90)
        print("【系統】早安圖在本地伺服器端完美繪製成功！")
        return True
    except Exception as e:
        print(f"【系統錯誤】繪圖邏輯崩潰，原因: {e}")
        return False

@app.route("/morning_image.jpg")
def serve_image():
    """ 讓您的 Render 伺服器自己當圖床，安全又不需要密鑰 """
    if os.path.exists(LOCAL_IMAGE_PATH):
        return send_file(LOCAL_IMAGE_PATH, mimetype="image/jpeg")
    return "Image not found.", 404

@app.route("/trigger")
def trigger():
    LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_USER_ID = os.environ.get("LINE_USER_ID")
    RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
    
    if not all([LINE_ACCESS_TOKEN, LINE_USER_ID]):
        return "【錯誤】Render 後台的 LINE 變數尚未設定，請檢查環境變數！"
        
    if not RENDER_EXTERNAL_URL:
        RENDER_EXTERNAL_URL = "https://" + requests.headers.get('Host', '')

    # 1. 執行純本地繪圖
    if not generate_morning_image():
        return "【失敗】圖片在加工時被系統阻擋。"
        
    # 2. 加上獨家防快取機制：用當前秒數當後綴（?t=1718320000）
    # 這樣 LINE 看到網址不一樣，就會強迫手機更新，圖片绝对會改變！
    timestamp = int(time.time())
    final_image_url = f"{RENDER_EXTERNAL_URL.rstrip('/')}/morning_image.jpg?t={timestamp}"
    print(f"【即將傳送給 LINE 的新鮮網址】: {final_image_url}")

    # 3. 推播至您的手機
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
        return "【恭喜吳大哥！大成功】文字自動換行、永不切邊的精美早安圖已成功發送！"
    else:
        return f"【發送失敗】LINE 伺服器拒絕連線，代碼: {line_res.status_code}，請確認 Token 是否過期。"

@app.route("/")
def home():
    return "The Ultimate Bulletproof Morning Bot is running beautifully!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
