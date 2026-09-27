import streamlit as st
from google import genai
from google.genai import types

# Sayfa Yapılandırması
st.set_page_config(page_title="Gemini AI Asistanı", page_icon="🤖")
st.title("🤖 Gemini Yapay Zeka Asistanı")

# Streamlit Secrets üzerinden API Anahtarını al
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("API Anahtarı bulunamadı! Lütfen Streamlit Secrets ayarlarını kontrol edin.")
    st.stop()

# Yeni resmi Google GenAI istemcisini başlat
client = genai.Client(api_key=api_key)

# Türkçe yanıt verme zorunluluğu için sistem talimatı
config = types.GenerateContentConfig(
    system_instruction="Sen her zaman Türkçe cevap veren yardımsever ve arkadaş canlısı bir yapay zeka asistanısın."
)

# Geçmiş mesajları hafızada tutma
if "messages" not in st.session_state:
    st.session_state.messages = []

# Eski mesajları ekrana çizdirme
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
            
            # Ana Model Denemesi
            try:
                response = client.models.generate_content(
                    model='gemini-3.8-flash',
                    contents=prompt,
                    config=config
                )
                bot_response = response.text
            except Exception:
                # 503 veya sunucu hatası durumunda sessizce yedek modele geçiş
                try:
                    response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=prompt,
                        config=config
                    )
                    bot_response = response.text
                except Exception as e:
                    st.error("Sunucular şu an çok yoğun, lütfen birkaç saniye sonra tekrar deneyin.")

            if bot_response:
                st.markdown(bot_response)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
