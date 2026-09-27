import streamlit as st
from google import genai
from google.genai import types

# Sayfa Yapılandırması
st.set_page_config(page_title="Gemini AI Asistanı", page_icon="🤖")
st.title("🤖 Gemini Yapay Zeka Asistanı")

# API Anahtarını Streamlit Secrets üzerinden alma
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("API Anahtarı Streamlit Secrets içinde bulunamadı!")
    st.stop()

# İstemciyi başlat
client = genai.Client(api_key=api_key)

# Türkçe yanıt verme zorunluluğu için sistem talimatı
config = types.GenerateContentConfig(
    system_instruction="Sen her zaman Türkçe cevap veren yardımsever ve arkadaş canlısı bir yapay zeka asistanısın."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Eski mesajları çizdirme
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Kullanıcıdan mesaj alma
if prompt := st.chat_input("Bir şeyler yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor..."):
            bot_response = None
            
            # 1. Deneme: En güncel ve hızlı flash modeli
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=config
                )
                bot_response = response.text
            except Exception as e1:
                # 2. Deneme: Yoğunluk/bulunamama durumunda yedek model
                try:
                    response = client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=prompt,
                        config=config
                    )
                    bot_response = response.text
                except Exception as e2:
                    st.error(f"Baglanti Hatasi: {str(e1)}")

            if bot_response:
                st.markdown(bot_response)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
