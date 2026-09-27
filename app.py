import streamlit as st
import time
from google import genai
from google.genai import types

# Sayfa Yapılandırması
st.set_page_config(page_title="Gemini AI Asistanı", page_icon="🤖")
st.title("🤖 Gemini Yapay Zeka Asistanı")

# API Anahtarını al
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("API Anahtarı Streamlit Secrets içinde bulunamadı!")
    st.stop()

client = genai.Client(api_key=api_key)

config = types.GenerateContentConfig(
    system_instruction="Sen her zaman Türkçe cevap veren yardımsever ve arkadaş canlısı bir yapay zeka asistanısın."
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Geçmiş mesajları ekrana çizdir
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Kullanıcı mesajı
if prompt := st.chat_input("Bir şeyler yazın..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Düşünüyor..."):
            bot_response = None
            max_retries = 3
            
            # Anlık 503 yoğunluk hatalarına karşı otomatik tekrar deneme (Retry)
            for attempt in range(max_retries):
                try:
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=prompt,
                        config=config
                    )
                    bot_response = response.text
                    break  # Başarılı olursa döngüden çık
                except Exception as e:
                    if "503" in str(e) and attempt < max_retries - 1:
                        time.sleep(1.5)  # Yoğunluk varsa 1.5 saniye bekle ve tekrar dene
                    else:
                        st.error("Sunucular şu an aşırı yoğun, lütfen birkaç saniye sonra tekrar mesaj gönderin.")
                        break

            if bot_response:
                st.markdown(bot_response)
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
