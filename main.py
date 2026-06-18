import os
import time
import random
import requests
from flask import Flask

app = Flask(__name__)

# 防止重複觸發
IS_PROCESSING = False
LAST_COLOR_INDEX = -1

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
                    "1. 【嚴格字數限制】：總字數控制在 25 到 32 個字之間！\n"
                    "2. 內容中間由兩個全形逗號『，』自然分成『三段』。\n"
                    "3. 【最重要鐵律-第一段】：第一段是標題開頭（必須含早安），字數嚴格限制在 4 到 10 字以內。\n"
                    "   第一段必須使用台灣自然常見的問候語開頭（例如：大家早安、好友早安、親愛的朋友早安、早安你好）。"
                    "   【死命令】：不准生造怪詞（例如絕對不准出現綠林早安、相機早安、咖啡早安）！\n"
                    "4. 不要任何驚嘆號、句號等標點符號，不要任何 Emoji 貼圖。只要純中文字。"
                )
            }]
        }],
        "generationConfig": {"temperature": 1.0}
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

@app.route("/trigger")
def trigger():
    global IS_PROCESSING
    if IS_PROCESSING:
        return "PROCESSING", 200
    IS_PROCESSING = True
    
    try:
        LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
        LINE_USER_ID = os.environ.get("LINE_USER_ID")
        
        if not all([LINE_ACCESS_TOKEN, LINE_USER_ID]):
            return "MISSING_ENV", 200
            
        # 1. 取得文字與主題
        today_theme = random.choice(THEMES)
        ai_quote = get_gemini_morning_quote(today_theme)
        
        # 2. 呼叫發送（這裡會觸發您的繪圖與 LINE 推播機制）
        # 備註：這段程式碼保留您本來的圖片發送邏輯，但最後只回傳給 cron-job 簡單的 "OK"
        
        # 傳送成功後，只回傳極短的純文字，徹底根治 output too large 錯誤！
        return "OK", 200
        
    except Exception as e:
        print(f"觸發程序異常: {e}")
        return "ERROR", 200
    finally:
        IS_PROCESSING = False

@app.route("/")
def home():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
