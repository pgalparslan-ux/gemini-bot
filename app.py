import streamlit as st
from openai import OpenAI

# Sayfa Yapılandırması
st.set_page_config(
    page_title="VorpH AI",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- SAF OLED SİYAH / SIFIR MAVİ / MONOKROM TEMA ---
st.markdown("""
<style>
    /* Tam Zifiri OLED Siyah Arka Plan */
    .stApp {
        background-color: #000000 !important;
        color: #e0e0e0 !important;
    }
    
    /* Başlıklar */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px;
    }
    
    /* Sol Menü (Sidebar) */
    section[data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #1a1a1a !important;
    }
    
    /* Sohbet Mesaj Kapsayıcıları */
    [data-testid="stChatMessage"] {
        padding: 14px 18px !important;
        margin-bottom: 12px !important;
        border: none !important;
    }
    
    /* Kullanıcı Sohbet Balonu */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #111111 !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid #222222 !important;
    }
    
    /* VorpH Asistan Mesaj Balonu */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #050505 !important;
        color: #d0d0d0 !important;
        border-radius: 12px !important;
        border: 1px solid #181818 !important;
    }
    
    /* Giriş Kutusu (Input Box) */
    .stChatInputContainer {
        background-color: #0a0a0a !important;
        border-radius: 16px !important;
        border: 1px solid #222222 !important;
    }
    
    /* Mavi Odaklanma Çizgisini Beyaza Çevirme */
    .stChatInputContainer:focus-within {
        border-color: #555555 !important;
    }
    
    /* Mavi Bilgi Kartları ve Uyarılar (Mavilik Sıfırlandı) */
    .stAlert, div[data-baseweb="notification"] {
        background-color: #0a0a0a !important;
        border: 1px solid #222222 !important;
        color: #e0e0e0 !important;
        border-radius: 12px !important;
    }

    /* Form Elemanları, Selectbox ve Input Kutuları */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        background-color: #0a0a0a !important;
        border-color: #222222 !important;
        color: #ffffff !important;
    }

    div[data-baseweb="select"]:focus-within, 
    div[data-baseweb="input"]:focus-within {
        border-color: #555555 !important;
    }

    /* Buton Tasarımları */
    button {
        background-color: #111111 !important;
        color: #ffffff !important;
        border: 1px solid #222222 !important;
        border-radius: 10px !important;
    }
    
    button:hover {
        border-color: #555555 !important;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# API Anahtarını alma
api_key = st.secrets.get("OPENROUTER_API_KEY", "")

# --- YAN MENÜ (SIDEBAR) AYARLARI ---
with st.sidebar:
    st.title("Kontrol Paneli")
    st.markdown("---")
    
    # Kullanıcı İsmi Girişi
    user_name = st.text_input("İsminiz:", value=st.session_state.get("user_name", ""), placeholder="Adınızı giriniz...")
    if user_name:
        st.session_state.user_name = user_name

    st.markdown("---")

    # Sadece Aktif Ücretsiz Modeller
    model_choice = st.selectbox(
        "Model Seçimi:",
        [
            "google/gemini-2.0-flash-exp:free",
            "deepseek/deepseek-r1:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "qwen/qwen-2.5-coder-32b-instruct:free"
        ]
    )

    st.markdown("---")
    
    # Asistan Modu Seçimi
    personality = st.selectbox(
        "Asistan Modu:",
        ["Genel Asistan", "Yazılım Uzmanı", "Kısa ve Öz", "Resmi"]
    )
    
    name_prompt = f" Kullanıcının adı '{user_name}'. Yanıtlarında kullanıcıya ismiyle ('{user_name}') hitap et." if user_name else ""
    
    instructions = {
        "Genel Asistan": f"Sen Türkçe cevap veren yardımsever VorpH isimli yapay zeka asistanısın.{name_prompt}",
        "Yazılım Uzmanı": f"Sen VorpH'sın. Kıdemli bir yazılım geliştiricisisin. Türkçe, açık ve temiz kod örnekleri sun.{name_prompt}",
        "Kısa ve Öz": f"Sen VorpH'sın. Cevapların her zaman Türkçe, kısa ve net olsun.{name_prompt}",
        "Resmi": f"Sen VorpH'sın. Kurumsal ve saygılı bir Türkçe yapay zeka asistanısın.{name_prompt}"
    }
    
    system_instruction = instructions[personality]
    
    st.markdown("---")
    
    if st.button("Sohbeti Sıfırla", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    st.caption("Altyapı: OpenRouter API")

# API Anahtarı Kontrolü
if not api_key:
    st.error("API Anahtarı bulunamadı! Streamlit Secrets ayarlarını kontrol edin.")
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
st.title("VorpH")
st.caption("Gelişmiş Yapay Zeka Asistanı")

if "messages" not in st.session_state:
    st.session_state.messages = []

if len(st.session_state.messages) == 0:
    welcome_text = f"Merhaba **{user_name}**, ben VorpH. Nasıl yardımcı olabilirim?" if user_name else "Merhaba, ben VorpH. Sol menüden isminizi girebilir veya soru sorabilirsiniz."
    st.markdown(f"<div class='stAlert'>{welcome_text}</div>", unsafe_allow_html=True)

# Geçmiş Mesajları Çizdirme
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Kullanıcı Mesaj Girişi
if prompt := st.chat_input("VorpH'a sorun..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Yanıtlanıyor..."):
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
                st.error(f"Hata: {str(e)}")
