import io
import base64
import streamlit as st
from openai import OpenAI
from gtts import gTTS

# Sayfa Yapılandırması
st.set_page_config(
    page_title="VorpH AI",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- ZİFİRİ SİYAH / MONOKROM CSS ---
st.markdown("""
<style>
    .stApp {
        background-color: #000000 !important;
        color: #e0e0e0 !important;
    }
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px;
    }
    section[data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #1a1a1a !important;
    }
    [data-testid="stChatMessage"] {
        padding: 14px 18px !important;
        margin-bottom: 12px !important;
        border: none !important;
    }
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #111111 !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        border: 1px solid #222222 !important;
    }
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #050505 !important;
        color: #d0d0d0 !important;
        border-radius: 12px !important;
        border: 1px solid #181818 !important;
    }

    /* Profil İkonlarındaki Renkleri Siyah-Gri Yapma */
    [data-testid="stChatMessageAvatar"] {
        background-color: #1a1a1a !important;
        filter: grayscale(100%) brightness(0.8) !important;
        border-radius: 50% !important;
    }

    .stChatInputContainer {
        background-color: #0a0a0a !important;
        border-radius: 16px !important;
        border: 1px solid #222222 !important;
    }
    .stAlert, [data-testid="stAlert"] {
        background-color: #0a0a0a !important;
        border: 1px solid #222222 !important;
        color: #e0e0e0 !important;
        border-radius: 12px !important;
    }
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

# API Anahtarı
api_key = st.secrets.get("OPENROUTER_API_KEY", "")

# --- GİZLİ VE TÜRKÇE SES OYNATICI (15X HIZLI) ---
def play_audio_15x(text):
    try:
        tts = gTTS(text=text, lang='tr')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        
        # Sesi base64 formatına dönüştürerek gizli HTML etiketi ile 15x hızında çalıştırır
        b64_audio = base64.b64encode(fp.read()).decode()
        audio_html = f"""
            <audio autoplay style="display:none;" onplay="this.playbackRate = 15.0;">
                <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
            </audio>
        """
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception:
        pass

# --- SOL MENÜ (SIDEBAR) ---
with st.sidebar:
    st.title("Kontrol Paneli")
    st.markdown("---")
    
    user_name = st.text_input("İsminiz:", value=st.session_state.get("user_name", ""), placeholder="Adınızı giriniz...")
    if user_name:
        st.session_state.user_name = user_name

    st.markdown("---")
    
    enable_audio = st.toggle("🔊 Sesli Yanıt", value=True)
    
    st.markdown("---")
    
    personality = st.selectbox(
        "Asistan Modu:",
        ["Genel Asistan", "Detaylı Uzman", "Yazılım Uzmanı", "Resmi"]
    )
    
    name_prompt = f" Kullanıcının adı '{user_name}'." if user_name else ""
    system_instruction = f"Sen VorpH adında bir yapay zeka asistanısın.{name_prompt} Tüm yanıtlarını Türkçe olarak ver."
    
    st.markdown("---")
    
    if st.button("Sohbeti Sıfırla", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if not api_key:
    st.error("API Anahtarı bulunamadı!")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
    default_headers={"HTTP-Referer": "https://streamlit.io", "X-Title": "VorpH AI"}
)

# --- ANA SAYFA ---
st.title("VorpH AI")
st.caption("Yapay Zeka Asistanı")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Mesaj Geçmişi
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Model Seçim Fonksiyonu
def get_ai_response(messages_list):
    candidate_models = [
        "openrouter/auto",
        "google/gemini-2.0-flash-001",
        "meta-llama/llama-3.1-8b-instruct:free"
    ]
    for model_id in candidate_models:
        try:
            completion = client.chat.completions.create(model=model_id, messages=messages_list)
            return completion.choices[0].message.content
        except Exception:
            continue
    raise Exception("Modellere erişilemedi.")

# Mesaj Girişi
prompt = st.chat_input("VorpH'a sorun...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("VorpH düşünüyor..."):
            try:
                api_messages = [{"role": "system", "content": system_instruction}]
                for m in st.session_state.messages:
                    api_messages.append({"role": m["role"], "content": m["content"]})

                bot_response = get_ai_response(api_messages)
                st.markdown(bot_response)
                
                # Ses çubuğunu gizleyip 15x hızında arka planda oynatma
                if enable_audio:
                    play_audio_15x(bot_response)

                st.session_state.messages.append({"role": "assistant", "content": bot_response})

            except Exception as e:
                st.error(f"Hata oluştu: {str(e)}")
