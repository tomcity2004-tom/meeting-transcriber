import streamlit as st
import whisper
from docx import Document
from datetime import datetime
import torch
import tempfile
import os
import subprocess

# 安裝 ffmpeg（Streamlit Cloud 環境）
if not os.path.exists("/usr/bin/ffmpeg"):
    subprocess.run("apt-get update && apt-get install -y ffmpeg", shell=True)

st.set_page_config(page_title="會議紀要轉化器", layout="centered")
st.title("🎙️ 自動會議紀要與待辦轉化器")
st.markdown("**支援音檔 / 影片 • 粵語 / 普通話 / 英語**")

with st.sidebar:
    st.header("設定")
    model_name = st.selectbox(
        "選擇 Whisper 模型",
        options=["medium", "large-v3", "small"],
        index=0,
        help="推薦使用 medium"
    )

uploaded_file = st.file_uploader(
    "上傳會議音檔或影片",
    type=["mp3", "wav", "m4a", "mp4", "mov", "avi", "mkv"],
)

if uploaded_file:
    st.success(f"✅ 已上傳：{uploaded_file.name}")
    
    if st.button("🚀 開始轉錄", type="primary"):
        with st.spinner("正在轉錄中..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=uploaded_file.name) as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    temp_path = tmp.name

                @st.cache_resource
                def load_model(name):
                    return whisper.load_model(name)
                
                model = load_model(model_name)

                # 直接轉錄（Whisper 可接受多種格式）
                result = model.transcribe(temp_path, language=None)
                transcript = result["text"]

                st.subheader("📝 轉錄結果")
                st.text_area("完整逐字稿", transcript, height=400)

                # 生成 Word
                doc = Document()
                doc.add_heading('會議紀要與待辦事項', 0)
                doc.add_paragraph(f'日期：{datetime.now().strftime("%Y-%m-%d %H:%M")}')
                doc.add_paragraph(f'檔案：{uploaded_file.name}')
                doc.add_paragraph('='*50)
                doc.add_heading('📋 完整逐字稿', level=1)
                doc.add_paragraph(transcript)
                
                doc.add_page_break()
                doc.add_heading('✅ 待辦事項', level=1)
                doc.add_paragraph("請手動整理或使用 LLM 進一步提取")

                docx_name = f"會議紀要_{datetime.now().strftime('%Y%m%d_%H%M')}.docx"
                doc.save(docx_name)

                col1, col2 = st.columns(2)
                with col1:
                    with open(docx_name, "rb") as f:
                        st.download_button("📥 下載 Word 會議紀要", f, file_name=docx_name)
                with col2:
                    st.download_button("📥 下載 TXT", transcript, 
                                     file_name=f"逐字稿_{datetime.now().strftime('%Y%m%d_%H%M')}.txt")

            except Exception as e:
                st.error(f"錯誤：{str(e)}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if 'docx_name' in locals() and os.path.exists(docx_name):
                    os.remove(docx_name)
