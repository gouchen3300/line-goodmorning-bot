import os
import time
import requests
from flask import Flask, send_file
from PIL import Image, ImageDraw, ImageFont, ImageFilter

app = Flask(__name__)

LOCAL_IMAGE_PATH = "morning_output.jpg"
FONT_FILE_NAME = "morning.ttf"

IS_PROCESSING = False

# 【核心記憶機制】紀錄當前輪到第幾組制式圖（0~9），預設從第 0 組開始
CURRENT_INDEX = 0

# 【超豪華 10 組純台灣味輪流清單】文字全部校正，調色盤色彩繽紛，保證連點測試時絕不重複！
STATIC_ROUNDS = [
    {
        "text": "大家早安，保持微笑，今天也要超級快樂",
        "colors": ("#FFF700", "#FFFFFF", "#FF69B4")  # 亮檸檬黃 + 白 + 桃紅
    },
    {
        "text": "好友早安，清晨好問候，記得吃份溫暖早餐",
        "colors": ("#FFFFFF", "#FF4500", "#FFF700")  # 純白 + 橘紅 + 黃
    },
    {
        "text": "親愛的朋友早安，把煩惱拋開，迎接幸運的一天",
        "colors": ("#FF69B4", "#FFFFFF", "#FFFDD0")  # 玫瑰粉 + 白 + 奶油黃
    },
    {
        "text": "祝您早安，平安愉快，天天都有好心情喔",
        "colors": ("#FFFDD0", "#00FF7F", "#FFFFFF")  # 溫柔黃 + 森林綠 + 白
    },
    {
        "text": "早安你好，讓陽光帶走疲憊，迎接美好新起點",
        "colors": ("#00BFFF", "#FFFFFF", "#FFF700")  # 湛藍 + 白 + 亮黃
    },
    {
        "text": "大家早安，新的一天，快樂劈里啪啦向你狂奔",
        "colors": ("#FFFFFF", "#E1AD01", "#FF69B4")  # 純白 + 文青金 + 粉紅
    },
    {
        "text": "好友早安，元氣滿滿，幸福已經在悄悄敲門囉",
        "colors": ("#FF4500", "#FFFFFF", "#00FF7F")  # 亮麗紅 + 白 + 清新綠
    },
    {
        "text": "祝您早安，微笑常在，心想事成萬事都順心",
        "colors": ("#FFFF33", "#FF1493", "#FFFFFF")  # 閃亮黃 + 驚豔粉 + 白
    },
    {
        "text": "親愛的朋友早安，放鬆心情，享受悠閒的晨光序曲",
        "colors": ("#FFFFFF", "#00CED1", "#FFA500")  # 純白 + 湖水藍 + 活力橘
    },
    {
        "text": "早安你好，滿滿正能量，今天也是幸運滿分的一天",
        "colors": ("#FFFF00", "#FF69B4", "#FFFFFF")  # 金黃 + 玫瑰粉 + 純白
    }
]

def get_must_font(size):
    if os.path.exists(FONT_FILE_NAME):
        try:
            return ImageFont.truetype(FONT_FILE_NAME, size)
        except:
            pass
    return ImageFont.load_default()

def draw_single_skew_line(base_img, text, font, color, center_y, image_width, is_title=False):
    """ 獨立文字圖層大角度歪斜與完美置中機制 """
    try:
        text_w = ImageDraw.Draw(base_img).textlength(text, font=font)
    except:
        text_w = len(text) * font.size
    text_h = int(font.size * 1.2)

    pad = 40
    txt_img = Image.new("RGBA", (int(text_w + pad * 2), int(text_h + pad * 2)), (0, 0, 0, 0))
    txt_draw = ImageDraw.Draw(txt_img)

    # 陰影與描邊
    shadow_radius = 7 if is_title else 5
    for dx in range(-shadow_radius, shadow_radius + 1):
        for dy in range(-shadow_radius, shadow_radius + 1):
            if abs(dx) + abs(dy) <= shadow_radius:
                txt_draw.text((pad + dx, pad + dy), text, font=font, fill="black")
                
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            txt_draw.text((pad + dx, pad + dy), text, font=font, fill="#FFFFFF")
            
    txt_draw.text((pad, pad), text, font=font, fill=color)

    # 第一行標題正端，其餘行微歪斜增加活力
    skew_angle = 0.0 if is_title else -7.5

    rotated_txt = txt_img.rotate(skew_angle, resample=Image.BICUBIC, expand=True)
    r_w, r_h = rotated_txt.size
    
    base_img.paste(rotated_txt, ((image_width - r_w) // 2, center_y - r_h // 2), rotated_txt)

def generate_static_round_image(round_data):
    """ 【穩定製圖】隨機抓背景圖，若網路不穩抓不到就用高質感深色背景防卡死 """
    try:
        # 使用時間戳記隨機換圖片 ID，讓測試時每張背景都不同
        chosen_id = int(time.time()) % 400 + 100
        bg_url = f"https://picsum.photos/id/{chosen_id}/800/600"
        img_res = requests.get(bg_url, timeout=5, stream=True)
        if img_res.status_code == 200:
            img = Image.open(img_res.raw).convert("RGB")
        else:
            img = Image.new("RGB", (800, 600), "#2c3e50")
    except:
        img = Image.new("RGB", (800, 600), "#2c3e50")
        
    img = img.resize((800, 600))
    img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    text_content = round_data["text"]
    colors = round_data["colors"]
    image_width, _ = img.size

    # 切割文字
    if "，" in text_content:
        lines = [line.strip() for line in text_content.split("，") if line.strip()]
    else:
        third = len(text_content) // 3
        lines = [text_content[:third], text_content[third:third*2], text_content[third*2:]]

    while len(lines) < 3:
        lines.append("祝您平安愉快")

    font_line1 = get_must_font(60)
    font_line2 = get_must_font(36)
    font_line3 = get_must_font(38)

    # 黃金置中排版
    draw_single_skew_line(img, lines[0], font_line1, colors[0], 340, image_width, is_title=True)
    draw_single_skew_line(img, lines[1], font_line2, colors[1], 435, image_width, is_title=False)
    draw_single_skew_line(img, lines[2], font_line3, colors[2], 525, image_width, is_title=False)

    img.save(LOCAL_IMAGE_PATH, "JPEG", quality=95)

@app.route("/morning_image.jpg")
def serve_image():
    if os.path.exists(LOCAL_IMAGE_PATH):
        res = send_file(LOCAL_IMAGE_PATH, mimetype="image/jpeg")
        # 徹底停用瀏覽器與 LINE 的所有快取機制
        res.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        res.headers["Pragma"] = "no-cache"
        res.headers["Expires"] = "0"
        return res
    return "NotFound", 404

@app.route("/trigger")
def trigger():
    global IS_PROCESSING, CURRENT_INDEX
    if IS_PROCESSING:
        return "OK"
    IS_PROCESSING = True
    
    try:
        LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
        LINE_USER_ID = os.environ.get("LINE_USER_ID")
        RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL")
        
        if not all([LINE_ACCESS_TOKEN, LINE_USER_ID]):
            return "OK"
            
        if not RENDER_EXTERNAL_URL:
            RENDER_EXTERNAL_URL = "https://" + requests.headers.get('Host', '')

        # 【核心輪流邏輯】拿出當前輪到的這一組資料（文字 + 顏色）
        round_data = STATIC_ROUNDS[CURRENT_INDEX]
        
        # 畫圖
        generate_static_round_image(round_data)
        
        # 為了強制刷新 LINE 的快取，我們把當前編號直接塞進網址裡：?idx=0, ?idx=1...
        timestamp = int(time.time())
        final_image_url = f"{RENDER_EXTERNAL_URL.rstrip('/')}/morning_image.jpg?idx={CURRENT_INDEX}&t={timestamp}"

        # 【指引下一組】這一次用完，下一次自動換下一號，到了 10 就歸零
        CURRENT_INDEX = (CURRENT_INDEX + 1) % len(STATIC_ROUNDS)

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
        
        requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload, timeout=10)
        return "OK"
        
    except Exception as e:
        print(f"錯誤: {e}")
        return "OK"
    finally:
        IS_PROCESSING = False

@app.route("/")
def home():
    return "OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
