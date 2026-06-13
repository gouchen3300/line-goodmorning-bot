import os
import requests
from flask import Flask
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)

def download_font():
    """為了確保中文字完美呈現，如果主機沒有字體，自動下載開源中文字體"""
    font_path = "msjh.ttf"
    if not os.path.exists(font_path):
        print("【系統】正在下載精美中文字體...")
        # 下載開源的微軟正黑體/思源黑體替代字型
        font_url = "https://github.com/MelonRind/taiwan-fonts/raw/master/ttf/MicrosoftJhengHei-Regular.ttf"
        try:
            r = requests.get(font_url, timeout=30)
            with open(font_path, "wb") as f:
                f.write(r.content)
            print("【系統】字體下載完成！")
        except Exception as e:
            print(f"【字體錯誤】下載失敗: {e}，將使用系統預設字體（英文）。")
    return font_path

def generate_and_send_goodmorning_image():
    LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_USER_ID = os.environ.get("LINE_USER_ID")
    
    if not all([LINE_ACCESS_TOKEN, LINE_USER_ID]):
        return "【錯誤】環境變數設定不完整，請檢查 LINE 的 Token 與 ID！"
    
    # 溫馨正宗中文祝賀詞
    morning_text = "大家早安！祝您今天平安喜樂，順心如意☀️"
    
    try:
        # 1. 抓取經典高畫質晨曦風景底圖 (確保絕對成功不崩潰)
        print("【系統】正在讀取高畫質晨曦底圖...")
        bg_url = "https://images.unsplash.com/photo-1506744038136-46273834b3fb?q=80&w=800&auto=format&fit=crop"
        bg_response = requests.get(bg_url, timeout=15, stream=True)
        img = Image.open(bg_response.raw).convert("RGBA")
        
        # 2. 準備在圖片上畫精美中文字
        draw = ImageDraw.Draw(img)
        font_path = download_font()
        
        # 設定字體大小 (根據 800x533 的圖，大小 36 最完美)
        try:
            font = ImageFont.truetype(font_path, 36)
        except:
            font = ImageFont.load_default()
            
        # 計算文字寬高以達成「真．完美置中」
        text_bbox = draw.textbbox((0, 0), morning_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # 計算置中座標 (放在中下方，畫面最優雅)
        img_width, img_height = img.size
        x = (img_width - text_width) / 2
        y = img_height - text_height - 80  # 距離底部 80 像素
        
        # 畫一個優雅的半透明深色文字背景框，防止風景太亮看不清字
        pad = 15
        rect_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        rect_draw = ImageDraw.Draw(rect_layer)
        rect_draw.rectangle(
            [x - pad, y - pad, x + text_width + pad, y + text_height + pad],
            fill=(0, 0, 0, 100) # 黑色半透明
        )
        img = Image.alpha_composite(img, rect_layer).convert("RGB")
        
        # 把白色祝福文字真正燙上去
        draw = ImageDraw.Draw(img)
        draw.text((x, y), morning_text, fill=(255, 255, 255), font=font)
        
        # 將畫好的圖暫存到主機
        local_image_path = "output.jpg"
        img.save(local_image_path, "JPEG", quality=90)
        
        # 3. 透過 ImgBB 圖床純上傳這張完美合成圖
        print("【系統】圖片本地繪製完美！正在上傳至專屬圖床...")
        with open(local_image_path, "rb") as image_file:
            img_upload_res = requests.post(
                "https://api.imgbb.com/1/upload",
                params={"key": "6b7b62fb76ec295b9d36561cf02a8bf2"},
                files={"image": image_file},
                timeout=20
            )
        
        if img_upload_res.status_code == 200:
            final_image_url = img_upload_res.json()["data"]["url"]
            print(f"【完美置中圖網址】: {final_image_url}")
        else:
            return f"【圖床錯誤】上傳失敗，狀態碼: {img_upload_res.status_code}"
            
    except Exception as e:
        return f"【系統繪圖崩潰】原因: {e}"

    # 4. 將真正完美排版的圖發送到您的 LINE
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
    
    url = "https://api.line.me/v2/bot/message/push"
    line_res = requests.post(url, headers=headers, json=payload, timeout=15)
    
    if line_res.status_code == 200:
        return f"【大成功】終極置中早安圖已發送！"
    else:
        return f"【發送失敗】LINE 管道拒絕，狀態碼: {line_res.status_code}"

@app.route("/trigger")
def trigger():
    return generate_and_send_goodmorning_image()

@app.route("/")
def home():
    return "True Center-Text Good Morning Bot is Running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
