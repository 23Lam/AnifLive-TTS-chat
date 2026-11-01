import os
import re
import json
import requests
from openai import OpenAI
from playsound import playsound
import time

# ================= 設定區 =================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "請填入你的_DEEPSEEK_API_KEY")
if DEEPSEEK_API_KEY == "請填入你的_DEEPSEEK_API_KEY":
    print("⚠️ 警告：請先設定你的 DeepSeek API Key！")
    print("💡 你可以在程式碼中修改，或設定環境變數 DEEPSEEK_API_KEY")
    # 這裡可以選擇直接退出，或者讓使用者輸入
    DEEPSEEK_API_KEY = input("請輸入你的 DeepSeek API Key: ").strip()
TTS_API_URL = "http://127.0.0.1:9882/v1/audio/speech"
TTS_MODEL = "模型名稱" # 模型名稱
OUTPUT_FILE = "./sound/"

# 確保音訊輸出資料夾存在，避免報錯
if not os.path.exists(OUTPUT_FILE):
    os.makedirs(OUTPUT_FILE)

# 初始化 DeepSeek 客戶端 (使用 OpenAI SDK)
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

# 定義 AI 的角色與情緒規則
SYSTEM_PROMPT = """
你是一個名為「XX」的XX。請用簡短的XX回答使用者的問題（每次回覆不要超過兩句話，適合口語表達）。
請根據你說話的語氣，在回覆的「最開頭」加上對應的情緒標籤。
可用的情緒標籤有：[normal-1], [warm-1], [joy-1], [excited-1], [firm-1], [concern-1], [surprised-1], [questioning-1], [nervous-1], [sad-1], [teasing-1], [longing-1], [proud-1], [strict-1], [angry-1]。
格式必須嚴格為：[情緒標籤] 你的台詞
例如：[joy-1] 今日はいい天気だね！

"""
def parse_ai_response(response_text):
    """解析 AI 的回覆，分離出情緒標籤和純文字"""
    emotion = "normal-1"
    text = response_text
    
    # 尋找開頭的 [xxx-x]
    match = re.match(r"^\[([a-zA-Z0-9-]+)\]\s*(.*)", response_text, re.DOTALL)
    if match:
        emotion = match.group(1)
        text = match.group(2).strip()

    # 語言判斷：檢查是否包含日文假名 (平假名 \u3040-\u309F, 片假名 \u30A0-\u30FF)
    if re.search(r'[\u3040-\u30ff]', text):
        lang = "ja"
    # 如果沒有假名，但有中文字元，才判定為中文
    elif re.search(r'[\u4e00-\u9fff]', text):
        lang = "zh"
    else:
        # 預設語言（如果是全英文或數字等）
        lang = "ja"

    return emotion, text, lang

def generate_tts(text, emotion, language):
    """呼叫 AnifLive-TTS 生成語音"""
    payload = {
        "model": TTS_MODEL,
        "voice_profile": "default",
        "text": text,
        "language": language, # 使用動態判斷的語言
        "stream": False,
        "expression": {
            "enabled": True,
            "profile": emotion,
            "intensity": 0.8,
            "policy": "semantic-style"
        }
    }
    
    print(f"🎙️ 正在生成語音 (情緒: {emotion}, 語言: {language})...")
    try:
        response = requests.post(TTS_API_URL, json=payload)
        if response.status_code == 200:
            filename = f"{OUTPUT_FILE}temp_reply_{int(time.time())}.wav"
            with open(filename, "wb") as f:
                f.write(response.content)
            return filename
        else:
            print(f"❌ TTS 錯誤: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 無法連接 TTS API: {e}")
        return None

def main():
    print("========================================")
    print("🎵 AI 語音聊天機器人 (DeepSeek + AnifLive-TTS)")
    print("輸入 'quit' 或 'exit' 結束對話")
    print("========================================\n")
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    while True:
        user_input = input("👤 你說: ")
        if user_input.lower() in ['quit', 'exit']:
            break
        if not user_input.strip():
            continue
            
        messages.append({"role": "user", "content": user_input})
        
        print("🤖 XX正在思考...")
        try:
            # 1. 呼叫 DeepSeek
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )
            ai_reply_full = response.choices[0].message.content
            messages.append({"role": "assistant", "content": ai_reply_full})
            
            # 2. 解析情緒、台詞與語言
            emotion, clean_text, lang = parse_ai_response(ai_reply_full)
            print(f"📝 XX (文字) [{emotion}]: {clean_text}")
            
            # 3. 生成並播放語音
            audio_file = generate_tts(clean_text, emotion, lang)
            if audio_file:
                print("🔊 正在播放...")
                playsound(audio_file)
                
        except Exception as e:
            print(f"❌ 發生錯誤: {e}")
            messages.pop()

if __name__ == "__main__":
    main()