@echo off
chcp 65001 >nul
title AI 語音助手
echo ========================================
echo 🎵 正在啟動 AI 語音系統...
echo ========================================
echo ⚠️ 注意：請確保你已經安裝了 Python 與套件 (pip install -r requirements.txt)
echo ⚠️ 請確保 AnifLive-TTS API 已經在你的本機端啟動 (Port: 9882)
echo.

:: 直接使用系統的 Python 啟動 Streamlit，並開啟網頁
python -m streamlit run web_ui_app.py

pause