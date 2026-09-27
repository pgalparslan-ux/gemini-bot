import streamlit as st
import time
from openai import OpenAI

# Sayfa Yapılandırması
st.set_page_config(
    page_title="VorpH AI",
    page_icon="✨",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- SAF OLED SİYAH / TAM ZİFİRİ TEMA (#000000) ---
st.markdown("""
<style>
    /* Tam Zifiri OLED Siyah Arka Plan */
    .stApp {
        background-color: #000000 !important;
        color: #e0e0e0 !important;
    }
    
    /* Başlıklar */
    h1 {
        color: #ffffff !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px;
    }
    
    /* Sol Menü (Sidebar) */
    section[data-testid="stSidebar"] {
        background-color: #080808 !important;
        border-right: 1px solid #181818 !important;
    }
    
    /* Sohbet Mesaj Kapsayıcıları */
    [data-testid="stChatMessage"] {
        padding: 14px 18px !important;
        margin-bottom: 12px !important;
        border: none !important;
    }
    
    /* Kullanıcı Sohbet Balonu */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #121212 !important;
        color: #f0f0f0 !important;
        border-radius: 18px 18px 4px 18px !important;
        border: 1px solid #222222 !important;
    }
    
    /* VorpH Asistan Mesaj Balonu */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #0a0a0a !important;
        color: #e0e0e0 !important;
        border-radius: 18px 18px 18px 4px !important;
        border: 1px solid #1a1a1a !important;
    }
    
    /* Giriş Kutusu (Input Box) */
    .stChatInputContainer {
        background-color: #0a0a0a !important;
        border-radius: 28px !important;
        border: 1px solid #222222 !important;
    }
    
    .stChatInputContainer:focus-within {
        border-color: #3b82f6 !important;
    }
    
    /* Bilgi ve Uyarı Kartları */
    .stAlert {
        background-color: #0a0a0a !important;
        border: 1px solid #222222 !important;
        color: #e0e0e0 !important;
        border-radius: 16px !important;
    }

    /* Form Elemanları ve Kutular */
    div[data-baseweb="input"] {
        background-color: #000000 !important;
        border-color: #222222 !important;
        color: #ffffff !important;
    }
    
    div[data-baseweb="select"] {
        background-color: #000000 !important;
        border-color: #222222 !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# Streamlit Secrets üzerinden API Anahtarını alma
api_key = st.secrets.get("OPENROUTER_API_KEY", "")

# --- YAN MENÜ (SIDEBAR) AYARLARI ---
with st.sidebar:
    st.title("⚙️ Kontrol Paneli")
    st.markdown("---")
    
    # Kullanıcı İsmi Girişi
    user_name = st.text_input("👤 İsminiz:", value=st.session_state.get("user_name", ""), placeholder="Adınızı giriniz...")
    if user_name:
        st.session_state.user_name = user_name

    st.markdown("---")

    # Ücretsiz Model Seçici
    model_choice = st.selectbox(
        "🤖 Model Seçimi (Ücretsiz):",
        [
            "meta-llama/llama-3.3-70b-instruct:free",
            "deepseek/deepseek-r1:free",
            "google/gemini-2.0-flash-exp:free"
        ]
    )

    st.markdown("---")
    
    # Asistan Modu Seçimi
    personality = st.selectbox(
        "🎯 Asistan Modu:",
        ["Genel Asistan", "Yazılım & Kodlama Uzmanı", "Kısa ve Öz Cevaplar", "Resmi & Profesyonel"]
    )
    
    name_prompt = f" Kullanıcının adı '{user_name}'. Yanıtlarında kullanıcıya ismiyle ('{user_name}') samimi ve doğal bir şekilde hitap et." if user_name else ""
    
    instructions = {
        "Genel Asistan": f"Sen her zaman Türkçe cevap veren, samimi, arkadaş canlısı ve son derece yardımsever VorpH isimli yapay zeka asistanısın.{name_prompt}",
        "Yazılım & Kodlama Uzmanı": f"Sen VorpH'sın. Kıdemli bir yazılım geliştiricisisin. Türkçe, açık, temiz kod örnekleri ve teknik açıklamalar içeren yanıtlar ver.{name_prompt}",
        "Kısa ve Öz Cevaplar": f"Sen VorpH'sın. Cevapların her zaman Türkçe, kısa, maddeler halinde ve net olsun.{name_prompt}",
        "Resmi & Profesyonel": f"Sen VorpH'sın. Kurumsal ve son derece saygılı bir Türkçe yapay zeka asistanısın. Profesyonel bir dil kullan.{name_prompt}"
    }
    
    system_instruction = instructions[personality]
    
    st.markdown("---")
    
    if st.button("🗑️ Sohbeti Sıfırla", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    st.caption("🚀 Altyapı: **OpenRouter API**")
    st.caption("👨‍💻 Geliştirici: **Anonim**")

# API Anahtarı Kontrolü
if not api_key:
    st.error("API Anahtarı bulunamadı! Lütfen Streamlit Secrets (OPENROUTER_API_KEY) ayarlarını kontrol edin.")
    st.stop()

# OpenRouter İstemcisi
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={
        "HTTP-Referer": "https://streamlit.io",
        "X-Title": "VorpH AI"
    }
)

# --- ANA SAYFA ---
st.title("✨ VorpH")
st.caption("Gelişmiş Yapay Zeka Asistanı")

if "messages" not in st.session_state:
    st.session_state.messages = []

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
            try:
                api_messages = [{"role": "system", "content": system_instruction}]
                for m in st.session_state.messages:
                    api_messages.append({"role": m["role"], "content": m["content"]})

                completion = client.chat.completions.create(
                    model=model_choice,
                    messages=api_messages
                )
                
                bot_response = completion.choices[0].message.content
                st.markdown(bot_response)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})

            except Exception as e:
                st.error(f"Baglanti Hatasi: {str(e)}")
