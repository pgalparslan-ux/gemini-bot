import streamlit as st
from openai import OpenAI

# Sayfa Yapılandırması
st.set_page_config(
    page_title="VorpH AI",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- ZİFİRİ SİYAH / SIFIR RENK (MONOKROM) CSS ---
st.markdown("""
<style>
    /* OLED Siyah Arka Plan */
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
    
    /* Sohbet Balonları */
    [data-testid="stChatMessage"] {
        padding: 14px 18px !important;
        margin-bottom: 12px !important;
        border: none !important;
    }
    
    /* Kullanıcı Mesajı */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #111111 !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid #222222 !important;
    }
    
    /* Asistan Mesajı */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #050505 !important;
        color: #d0d0d0 !important;
        border-radius: 12px !important;
        border: 1px solid #181818 !important;
    }

    /* Profil İkonlarındaki Sarı ve Kırmızı Renkleri Siyaha/Siyah-Beyaza Çevirme */
    [data-testid="stChatMessageAvatar"] {
        background-color: #1a1a1a !important;
        filter: grayscale(100%) brightness(0.8) !important;
        border-radius: 50% !important;
    }
    
    /* Alt Yazma Kutusu (Ekranın En Altına Sabitlenir) */
    .stChatInputContainer {
        background-color: #0a0a0a !important;
        border-radius: 16px !important;
        border: 1px solid #222222 !important;
    }
    
    .stChatInputContainer:focus-within {
        border-color: #555555 !important;
    }

    /* Sarı, Kırmızı ve Mavi Hata/Uyarı Kutularını Siyaha Çevirme */
    .stAlert, [data-testid="stAlert"] {
        background-color: #0a0a0a !important;
        border: 1px solid #222222 !important;
        color: #e0e0e0 !important;
        border-radius: 12px !important;
    }
    
    .stAlert svg {
        fill: #888888 !important;
    }

    /* Input ve Selectbox Alanları */
    div[data-baseweb="input"] > div,
    div[data-baseweb="select"] > div {
        background-color: #0a0a0a !important;
        border-color: #222222 !important;
        color: #ffffff !important;
    }

    /* Butonlar */
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

# API Anahtarı Kontrolü
api_key = st.secrets.get("OPENROUTER_API_KEY", "")

# --- SOL MENÜ (SIDEBAR) ---
with st.sidebar:
    st.title("Kontrol Paneli")
    st.markdown("---")
    
    user_name = st.text_input("İsminiz:", value=st.session_state.get("user_name", ""), placeholder="Adınızı giriniz...")
    if user_name:
        st.session_state.user_name = user_name

    st.markdown("---")

    # Aktif Ücretsiz Modeller
    model_choice = st.selectbox(
        "Model Seçimi:",
        [
            "deepseek/deepseek-r1:free",
            "meta-llama/llama-3.1-8b-instruct:free",
            "qwen/qwen-2.5-coder-32b-instruct:free",
            "openrouter/auto"
        ]
    )

    st.markdown("---")
    
    personality = st.selectbox(
        "Asistan Modu:",
        ["Detaylı Uzman", "Genel Asistan", "Yazılım Uzmanı", "Resmi"]
    )
    
    name_prompt = f" Kullanıcının adı '{user_name}'." if user_name else ""
    
    # Tüm cevapların Türkçe, detaylı ve açıklayıcı olmasını sağlayan sistem talimatı
    instructions = {
        "Detaylı Uzman": (
            f"Sen VorpH adında üst düzey bir yapay zeka asistanısın.{name_prompt} "
            "TÜM YANITLARINI KESİNLİKLE TÜRKÇE OLARAK VER. "
            "Sorulan her konuyu derinlemesine incele, arka plan bilgisi sun, "
            "alt başlıklar, maddeler, detaylı açıklamalar ve örnekler ekleyerek eksiksiz bir şekilde yanıtla."
        ),
        "Genel Asistan": (
            f"Sen VorpH adında yardımsever bir yapay zeka asistanısın.{name_prompt} "
            "Tüm yanıtlarını her zaman akıcı, anlaşılır ve detaylı bir Türkçe ile ver."
        ),
        "Yazılım Uzmanı": (
            f"Sen VorpH adında kıdemli bir yazılım mimarısın.{name_prompt} "
            "Tüm teknik açıklamalarını ve kod örneklerini Türkçe olarak, detaylı açıklamalar ve yorum satırlarıyla birlikte sun."
        ),
        "Resmi": (
            f"Sen VorpH adında kurumsal bir yapay zeka asistanısın.{name_prompt} "
            "Tüm yanıtlarını resmi, saygılı, açıklayıcı ve detaylı bir Türkçe ile ver."
        )
    }
    
    system_instruction = instructions[personality]
    
    st.markdown("---")
    
    if st.button("Sohbeti Sıfırla", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    st.caption("Altyapı: OpenRouter API")

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
    welcome_text = f"Merhaba **{user_name}**, ben VorpH. Size detaylı ve kapsamlı bir şekilde nasıl yardımcı olabilirim?" if user_name else "Merhaba, ben VorpH. Sol menüden isminizi girebilir veya hemen sorularınızı sorabilirsiniz."
    st.markdown(f"<div class='stAlert'>{welcome_text}</div>", unsafe_allow_html=True)

# Geçmiş Mesajlar
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Alt Taraftaki Yazma Kutusu (Ekranın en altındadır)
if prompt := st.chat_input("VorpH'a detaylı bir soru sorun..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Detaylı yanıt hazırlanıyor..."):
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
                st.error(f"Hata oluştu: {str(e)}")
