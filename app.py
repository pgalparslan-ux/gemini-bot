import streamlit as st
import time
from google import genai
from google.genai import types

# Sayfa Ayarları ve Başlık Yapılandırması
st.set_page_config(
    page_title="Gemini AI Asistanı",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded"
)

# API Anahtarını Streamlit Secrets Üzerinden Alma
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("API Anahtarı Streamlit Secrets içinde bulunamadı!")
    st.stop()

# İstemciyi Başlat
client = genai.Client(api_key=api_key)

# --- YAN MENÜ (SIDEBAR) AYARLARI ---
with st.sidebar:
    st.title("⚙️ Kontrol Paneli")
    st.markdown("---")
    
    # Asistan Modu Seçimi
    personality = st.selectbox(
        "🎯 Asistan Modu:",
        ["Genel Asistan", "Yazılım & Kodlama Uzmanı", "Kısa ve Öz Cevaplar", "Resmi & Profesyonel"]
    )
    
    # Seçilen Moda Göre Sistem Talimatı Belirleme
    instructions = {
        "Genel Asistan": "Sen her zaman Türkçe cevap veren, samimi, arkadaş canlısı ve son derece yardımsever bir AI asistanısın.",
        "Yazılım & Kodlama Uzmanı": "Sen kıdemli bir yazılım geliştiricisisin. Türkçe, açık, temiz kod örnekleri ve teknik açıklamalar içeren yanıtlar ver.",
        "Kısa ve Öz Cevaplar": "Sen Türkçe yanıt veren bir asistansın. Cevapların her zaman kısa, maddeler halinde ve net olsun.",
        "Resmi & Profesyonel": "Sen kurumsal ve son derece saygılı bir Türkçe yapay zeka asistanısın. Profesyonel bir dil kullan."
    }
    
    system_instruction = instructions[personality]
    
    st.markdown("---")
    
    # Sohbet Temizleme Butonu
    if st.button("🗑️ Sohbeti Sıfırla", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    st.caption("🚀 Model: **gemini-3.8-flash**")
    st.caption("👨‍💻 Geliştirici: **Alparslan**")

# --- ANA SAYFA İÇERİĞİ ---
st.title("⚡ Gemini AI Asistanı")
st.caption("Google Gemini API & Streamlit ile güçlendirilmiş akıllı sohbet uygulaması")

# Sistem Yapılandırması
config = types.GenerateContentConfig(
    system_instruction=system_instruction
)

# Sohbet Geçmişini Hafızada Tutma
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sohbet Boşsa Karşılama Kartı Göster
if len(st.session_state.messages) == 0:
    st.info("👋 Merhaba! Sormak istediğiniz soruyu aşağıya yazabilir veya sol taraftan asistan modunu değiştirebilirsiniz.")

# Geçmiş Mesajları Ekrana Çizdirme
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Kullanıcıdan Mesaj Alma
if prompt := st.chat_input("Bir şeyler yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Yanıt hazırlanıyor..."):
            bot_response = None
            max_retries = 3
            
            # Anlık 503 yoğunluk hatalarına karşı otomatik tekrar deneme
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=prompt,
                        config=config
                    )
                    bot_response = response.text
                    break
                except Exception as e:
                    if "503" in str(e) and attempt < max_retries - 1:
                        time.sleep(1.5)
                    else:
                        st.error("Sunucular şu an aşırı yoğun, lütfen birkaç saniye sonra tekrar deneyin.")
                        break

            if bot_response:
                st.markdown(bot_response)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
