import streamlit as st
import time
from google import genai
from google.genai import types

# Sayfa Yapılandırması
st.set_page_config(
    page_title="VorpH AI",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- ÖZEL ARAYÜZ / SOHBET BALONLARI VE TEMA KODLARI (CSS) ---
st.markdown("""
<style>
    /* Arka Plan Rengi ve Fontlar */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }
    
    /* Üst Başlık Stilizasyonu */
    h1 {
        color: #38bdf8 !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }

    /* Sohbet Balonları Tasarımı */
    [data-testid="stChatMessage"] {
        border-radius: 18px;
        padding: 12px 18px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }

    /* Kullanıcı Sohbet Balonu */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #1e3a8a;
        border: 1px solid #3b82f6;
    }

    /* Asistan Sohbet Balonu */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #334155;
        border: 1px solid #475569;
    }

    /* Sol Menü (Sidebar) Stilizasyonu */
    section[data-testid="stSidebar"] {
        background-color: #090d16;
        border-right: 1px solid #1e293b;
    }

    /* Input Giriş Kutusu */
    .stChatInputContainer {
        border-radius: 15px;
        border: 1px solid #38bdf8 !important;
    }
</style>
""", unsafe_allow_html=True)

# API Anahtarını Alma
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
    
    instructions = {
        "Genel Asistan": "Sen her zaman Türkçe cevap veren, samimi, arkadaş canlısı ve son derece yardımsever VorpH isimli yapay zeka asistanısın.",
        "Yazılım & Kodlama Uzmanı": "Sen VorpH'sın. Kıdemli bir yazılım geliştiricisisin. Türkçe, açık, temiz kod örnekleri ve teknik açıklamalar içeren yanıtlar ver.",
        "Kısa ve Öz Cevaplar": "Sen VorpH'sın. Cevapların her zaman Türkçe, kısa, maddeler halinde ve net olsun.",
        "Resmi & Profesyonel": "Sen VorpH'sın. Kurumsal ve son derece saygılı bir Türkçe yapay zeka asistanısın. Profesyonel bir dil kullan."
    }
    
    system_instruction = instructions[personality]
    
    st.markdown("---")
    
    # Sohbet Temizleme Butonu
    if st.button("🗑️ Sohbeti Sıfırla", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    st.caption("🚀 Model: **gemini-3.8-flash**")
    st.caption("👨‍💻 Geliştirici: **Anonim**")

# --- ANA SAYFA ---
st.title("⚡ VorpH")
st.caption("Gelişmiş Yapay Zeka Asistanı")

config = types.GenerateContentConfig(
    system_instruction=system_instruction
)

# Sohbet Geçmişi
if "messages" not in st.session_state:
    st.session_state.messages = []

# Karşılama Kartı
if len(st.session_state.messages) == 0:
    st.info("👋 Merhaba! Ben **VorpH**. Nasıl yardımcı olabilirim?")

# Geçmiş Mesajları Balon Şeklinde Çizdirme
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Kullanıcı Mesaj Girişi
if prompt := st.chat_input("VorpH'a bir şeyler sorun..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("VorpH yanıtlıyor..."):
            bot_response = None
            max_retries = 3
            
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
