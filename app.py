import streamlit as st
import time
from google import genai
from google.genai import types

# Sayfa Yapılandırması
st.set_page_config(
    page_title="VorpH AI",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- GEMINI TEMASI (CSS) ---
st.markdown("""
<style>
    .stApp {
        background-color: #131314 !important;
        color: #e3e3e3 !important;
    }
    h1 {
        color: #e3e3e3 !important;
        font-weight: 500 !important;
        letter-spacing: -0.5px;
    }
    section[data-testid="stSidebar"] {
        background-color: #1e1f20 !important;
        border-right: 1px solid #282a2c !important;
    }
    [data-testid="stChatMessage"] {
        padding: 14px 18px !important;
        margin-bottom: 12px !important;
        border: none !important;
    }
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #282a2c !important;
        color: #e3e3e3 !important;
        border-radius: 20px 20px 4px 20px !important;
    }
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #1e1f20 !important;
        color: #e3e3e3 !important;
        border-radius: 20px 20px 20px 4px !important;
    }
    .stChatInputContainer {
        background-color: #1e1f20 !important;
        border-radius: 28px !important;
        border: 1px solid #3c4043 !important;
    }
    .stChatInputContainer:focus-within {
        border-color: #a8c7fa !important;
    }
    .stAlert {
        background-color: #1e1f20 !important;
        border: 1px solid #3c4043 !important;
        color: #e3e3e3 !important;
        border-radius: 16px !important;
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
    
    # Kullanıcı İsmi Girişi
    user_name = st.text_input("👤 İsminiz:", value=st.session_state.get("user_name", ""), placeholder="Adınızı giriniz...")
    if user_name:
        st.session_state.user_name = user_name

    st.markdown("---")
    
    # Asistan Modu Seçimi
    personality = st.selectbox(
        "🎯 Asistan Modu:",
        ["Genel Asistan", "Yazılım & Kodlama Uzmanı", "Kısa ve Öz Cevaplar", "Resmi & Profesyonel"]
    )
    
    # İsme Göre Dinamik Sistem Talimatı
    name_prompt = f" Kullanıcının adı '{user_name}'. Yanıtlarında kullanıcıya ismiyle ('{user_name}') samimi ve doğal bir şekilde hitap et." if user_name else ""
    
    instructions = {
        "Genel Asistan": f"Sen her zaman Türkçe cevap veren, samimi, arkadaş canlısı ve son derece yardımsever VorpH isimli yapay zeka asistanısın.{name_prompt}",
        "Yazılım & Kodlama Uzmanı": f"Sen VorpH'sın. Kıdemli bir yazılım geliştiricisisin. Türkçe, açık, temiz kod örnekleri ve teknik açıklamalar içeren yanıtlar ver.{name_prompt}",
        "Kısa ve Öz Cevaplar": f"Sen VorpH'sın. Cevapların her zaman Türkçe, kısa, maddeler halinde ve net olsun.{name_prompt}",
        "Resmi & Profesyonel": f"Sen VorpH'sın. Kurumsal ve son derece saygılı bir Türkçe yapay zeka asistanısın. Profesyonel bir dil kullan.{name_prompt}"
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
st.title("✨ VorpH")
st.caption("Gelişmiş Yapay Zeka Asistanı")

config = types.GenerateContentConfig(
    system_instruction=system_instruction
)

# Sohbet Geçmişi
if "messages" not in st.session_state:
    st.session_state.messages = []

# Karşılama Kartı
if len(st.session_state.messages) == 0:
    welcome_text = f"👋 Merhaba **{user_name}**! Ben **VorpH**. Bugün sana nasıl yardımcı olabilirim?" if user_name else "👋 Merhaba! Ben **VorpH**. Lütfen sol menüden isminizi girin veya doğrudan soru sormaya başlayın."
    st.info(welcome_text)

# Geçmiş Mesajları Çizdirme
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "✨"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Kullanıcı Mesaj Girişi
if prompt := st.chat_input("VorpH'a bir şeyler sorun..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="✨"):
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
                    err_str = str(e)
                    # Hem 503 (Yoğunluk) hem 429 (Kota/Rate limit) durumlarında otomatik tekrar dene
                    if any(code in err_str for code in ["503", "429", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]) and attempt < max_retries - 1:
                        time.sleep(2)  # 2 saniye bekle
                    else:
                        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                            st.error("⚠️ Dakikalık kullanım kotası doldu. Lütfen 30 saniye bekleyip tekrar deneyin.")
                        elif "503" in err_str or "UNAVAILABLE" in err_str:
                            st.error("⚠️ Sunucular anlık olarak yoğun. Lütfen birkaç saniye sonra tekrar deneyin.")
                        else:
                            st.error(f"Baglanti Hatasi: {err_str}")
                        break

            if bot_response:
                st.markdown(bot_response)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
