import os
import re
import time
import requests
import streamlit as st
from openai import OpenAI
from pydub import AudioSegment


from chat_with_deepseek import parse_ai_response, generate_tts

# ================= 設定區 =================
with st.sidebar:
    st.header("⚙️ 設定")
    DEEPSEEK_API_KEY = st.text_input("DeepSeek API Key", type="password", help="請輸入你的 sk- 開頭的 API Key")
    if not DEEPSEEK_API_KEY:
        st.warning("請先在左側輸入 API Key 才能開始聊天！")
        st.stop() # 如果沒有輸入 Key，網頁就停在這裡
TTS_API_URL = "http://127.0.0.1:9882/v1/audio/speech"
TTS_MODEL = "模型名稱" # 模型名稱
OUTPUT_FILE = "./sound/"

# 確保音訊輸出資料夾存在，避免報錯
if not os.path.exists(OUTPUT_FILE):
    os.makedirs(OUTPUT_FILE)

# 初始化 DeepSeek 客戶端
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

# ================= Streamlit UI =================
st.set_page_config(page_title="AI 聊天室", page_icon="🎸", layout="centered")

st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .stAudio { margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("AI 語音助手")
st.caption("DeepSeek + AnifLive-TTS 本地語音引擎")

# 初始化對話歷史
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
if "display_messages" not in st.session_state:
    st.session_state.display_messages = []

# 顯示歷史對話
for msg in st.session_state.display_messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🎸"):
        st.write(msg["content"])
        if "audio" in msg and os.path.exists(msg["audio"]):
            st.audio(msg["audio"], format="audio/wav")

# 接收使用者輸入
if prompt := st.chat_input("跟XX說點什麼..."):
    # 顯示使用者訊息並存入歷史
    st.session_state.display_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.write(prompt)

    # AI 回覆區塊
    with st.chat_message("assistant", avatar="🎸"):
        with st.spinner("XX正在思考..."):
            # 呼叫 DeepSeek
            st.session_state.messages.append({"role": "user", "content": prompt})
            try:
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=st.session_state.messages,
                    temperature=0.7,
                    max_tokens=150
                )
                ai_reply_full = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": ai_reply_full})
            except Exception as e:
                st.error(f"DeepSeek 發生錯誤: {e}")
                st.stop()

            # 解析情緒與語言
            emotion, clean_text, lang = parse_ai_response(ai_reply_full)

            # 顯示文字
            st.write(clean_text)

            # 生成語音並播放
            audio_file = generate_tts(clean_text, emotion, lang)
            if audio_file and os.path.exists(audio_file):
                st.audio(audio_file, format="audio/wav", autoplay=True)
                # 將這輪對話存入歷史紀錄（包含音檔路徑）
                st.session_state.display_messages.append({
                    "role": "assistant",
                    "content": clean_text,
                    "audio": audio_file
                })