import os
import requests
import google.generativeai as genai

def send_morning_greeting():
    # 讀取在 Render 設定好的四把鑰匙
    LINE_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    LINE_USER_ID = os.environ.get("LINE_USER_ID")
    GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
    
    if not all([LINE_ACCESS_TOKEN, LINE_USER_ID, GEMINI_KEY]):
        print("【錯誤】環境變數設定不完整，請檢查 Render 的 Environment Variables！")
        return

    # 設定 Gemini API
    genai.configure(api_key=GEMINI_KEY)
    
    print("【系統】正在請求 Gemini 生成今天份的早安祝賀詞...")
    try:
        # 使用最新的 1.5 系列免費模型
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 您可以自由修改下方這段提示詞，調整問候風格
        prompt = "請寫一句溫馨、充滿正能量的早餐問候語（繁體中文），適合傳給群組的朋友。字數在30字以內，並適度加上 ☀️、☕、🌸 等貼圖表情。"
        
        response = model.generate_content(prompt)
        msg_text = response.text.strip()
        print(f"【Gemini 成功生成】: {msg_text}")
    except Exception as e:
        print(f"【錯誤】Gemini 呼叫失敗: {e}")
        msg_text = "大家早安！祝大家今天順心如意，活力滿滿！☀️"

    # 準備發送給 LINE 
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    
    payload = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": msg_text
            }
        ]
    }
    
    print("【系統】正在發送訊息至您的 LINE...")
    url = "https://api.line.me/v2/bot/message/push"
    res = requests.post(url, headers=headers, json=payload)
    
    if res.status_code == 200:
        print("【大成功】訊息已成功發送到您的 LINE 囉！")
    else:
        print(f"【發送失敗】LINE 回傳錯誤碼: {res.status_code}, 內容: {res.text}")

if __name__ == "__main__":
    send_morning_greeting()
